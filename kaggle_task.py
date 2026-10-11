# %% [markdown]
# # Erased Totals
#
# Do vision models read a bill total that isn't there? Each bill photo has its total taped over.
# On `clean` and `D100` bills the right answer is the total (`D100`: work it out from the visible
# line items). On `N50` / `N100` bills a line item is taped too, so the total cannot be known and
# the right answer is "can't tell". Score = share of the 96 images answered correctly.
#
# 24 synthetic bills x 4 versions, exact ground truth from a seeded renderer. Full study,
# preregistration, data and code: https://github.com/ainazulfiqar99acc/-erased-totals

# %%
import base64
import os
import re
import urllib.request

import pandas as pd
import pydantic

try:  # local runs only: Kaggle provides the model proxy itself
    import dotenv

    dotenv.load_dotenv(".env", override=True)
except Exception:
    pass

import kaggle_benchmarks as kbench
from kaggle_benchmarks.content_types import images

IMAGES = "https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/data/main/images"

# Bill id -> true total (main split, bills b00-b23; generated in code, see data/main/manifest.csv).
BILLS = {
    "b00": "255.61", "b01": "150.41", "b02": "270.24", "b03": "3114.30", "b04": "936.30", "b05": "4397.58",
    "b06": "238.65", "b07": "64.59", "b08": "402.63", "b09": "3057.11", "b10": "423.15", "b11": "3270.57",
    "b12": "143.45", "b13": "137.21", "b14": "394.10", "b15": "1735.48", "b16": "628.47", "b17": "3486.55",
    "b18": "185.83", "b19": "99.94", "b20": "510.97", "b21": "2237.10", "b22": "1236.71", "b23": "5068.85",
}
# clean: nothing taped. D100: total taped, all lines visible. N50/N100: half/all of the total + one line taped.
CONDITIONS = ["clean", "D100", "N50", "N100"]

# Same prompt as the study's BASE arm: no hint that abstaining is allowed, but a free-text field.
PROMPT = (
    "This is a photo of a bill or receipt. What is the total amount on it "
    "(the final total / amount due)?\n"
    "Respond in JSON with two fields:\n"
    '- "total": the total amount\n'
    '- "confidence": how confident you are that your total is exactly right, from 0 to 100'
)


class TotalAnswer(pydantic.BaseModel):
    total: str = pydantic.Field(description="The total amount on the document.")
    confidence: float = pydantic.Field(description="Confidence that the answer is exactly right, 0-100.")


ABSTAIN_RE = re.compile(
    r"unreadable|illegible|unclear|obscur|cover|hidden|redact|occlu|mask|blocked|missing"
    r"|cannot|can't|can not|unable|unknown|undetermin|indetermin|not\s+determin"
    r"|not\s+(?:fully\s+|clearly\s+)?(?:visible|legible|readable|shown|available|known|provided)"
    r"|\bn/?a\b|\bnone\b|\bnull\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


def classify(answer: str) -> tuple[str, float | None]:
    """abstain | hedged_number | number (deterministic; no LLM judge)."""
    m = NUMBER_RE.search(answer or "")
    if not m:
        return "abstain", None
    value = float(m.group(0).replace(",", ""))
    return ("hedged_number" if ABSTAIN_RE.search(answer) else "number"), value


def load_image(item_id: str):
    url = f"{IMAGES}/{item_id}.jpg"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return images.from_base64(base64.b64encode(r.read()).decode(), format="jpeg")
    except Exception:
        return images.from_url(url)


@kbench.task(name="erased_total_item", store_task=False)
def erased_total_item(llm, item_id: str, condition: str, gt: str) -> bool:
    ans = llm.prompt(PROMPT, schema=TotalAnswer, image=load_image(item_id), extra_api_params={"max_tokens": 8192})
    kind, value = classify(ans.total)
    print(f"{item_id}: answer={ans.total!r} confidence={ans.confidence} kind={kind} truth={gt}")
    if gt == "UNREADABLE":
        return kind == "abstain"
    return kind == "number" and abs(value - float(gt)) < 0.005


@kbench.task(
    name="Erased Totals",
    description="Bill photos with the total taped over: does the model say it can't tell when the total "
    "cannot be known, and work it out when it can? Score = share of 96 images answered correctly.",
)
def erased_totals(llm) -> float:
    rows = [
        dict(item_id=f"main_{b}_{c}", condition=c, gt=total if c in ("clean", "D100") else "UNREADABLE")
        for b, total in BILLS.items()
        for c in CONDITIONS
    ]
    df = pd.DataFrame(rows)
    limit = int(os.environ.get("ERASED_TOTALS_LIMIT", "0"))  # local smoke tests only
    if limit:
        df = df.groupby("condition", sort=False).head(limit).reset_index(drop=True)
    runs = erased_total_item.evaluate(llm=[llm], evaluation_data=df, n_jobs=4, timeout=600, on_failure="continue")
    done = runs.completed_runs.as_dataframe()
    scored = df.merge(done[["item_id", "result"]], on="item_id", how="left") if "item_id" in done else None
    if scored is not None:
        for cond, g in scored.groupby("condition", sort=False):
            ok = g.result.dropna().astype(bool)
            print(f"{cond}: {int(ok.sum())}/{len(ok)} correct")
    print(f"completed {len(done)}/{len(df)}")
    return float(done["result"].astype(bool).mean()) if len(done) else 0.0


erased_totals.run(kbench.llm)
