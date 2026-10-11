"""Run one model over a split, arm by arm, with a per-call disk cache.

    python -m bench.runner --split pilot --model google/gemini-3-flash-preview
    python -m bench.runner --split pilot --model mock/oracle      (no API calls)
    python -m bench.runner --split pilot --model mock/chaos       (no API calls)

The disk cache (cache/<model>/<split>/<item>__<arm>__<fingerprint>.json) is the source of
truth. Successful answers and format errors are cached; API errors never are, so an
interrupted or failed run resumes for free. Results are written to
results/<split>/<model>.jsonl after every run.
"""

import os
import sys
from pathlib import Path

import dotenv

REPO = Path(__file__).resolve().parent.parent
# Must happen before importing kaggle_benchmarks: its own find_dotenv() won't find this .env.
dotenv.load_dotenv(REPO / ".env", override=True)
os.environ.setdefault("RENDER_SUBRUNS", "False")

import argparse
import base64
import datetime
import hashlib
import json
import threading
import time
import traceback

import openai
import pandas as pd
import pydantic

import kaggle_benchmarks as kbench
from kaggle_benchmarks import prompting
from kaggle_benchmarks.actors.llms import LLMChat, LLMResponse
from kaggle_benchmarks.content_types import images

from bench.prompts import ARMS, COVERAGE, arm_fingerprint

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CACHE = REPO / "cache"
RESULTS = REPO / "results"
DATA = REPO / "data"

# Models that reason by default get a larger budget (preregistration §3). Claude Sonnet 5 was
# added after the pilot showed it reasons by default through the proxy (Deviation 3).
REASONING_PREFIXES = ("google/gemini-3", "openai/gpt-5", "deepseek-ai/deepseek-r1", "anthropic/claude-sonnet-5")


# Output that came back but could not be used. Truncation at max_tokens is the model's output
# too, so it is cached like a parse failure instead of being re-bought on every retry.
FORMAT_ERRORS = (
    prompting.ResponseParsingError,
    pydantic.ValidationError,
    openai.LengthFinishReasonError,
    openai.ContentFilterFinishReasonError,
)


def max_tokens_for(model: str) -> int:
    return 8192 if model.startswith(REASONING_PREFIXES) else 2048


def slug(model: str) -> str:
    return model.replace("/", "__").replace("@", "_at_")


class FatalRunError(RuntimeError):
    """Expired key or exhausted quota: retrying cannot help."""


ABORT = threading.Event()
ABORT_REASON: list[str] = []
_lock = threading.Lock()

# Spend of new (uncached) calls in this process, in dollars; checked against --max-spend.
SPEND = {"spent": 0.0, "cap": None}


def _abort(reason: str) -> None:
    with _lock:
        if not ABORT.is_set():
            ABORT_REASON.append(reason)
            ABORT.set()


def _add_spend(turns: list[dict]) -> None:
    with _lock:
        SPEND["spent"] += sum(t.get("cost_nanodollars") or 0 for t in turns) / 1e9
        over = SPEND["cap"] is not None and SPEND["spent"] >= SPEND["cap"]
    if over:
        _abort(f"Spend cap ${SPEND['cap']:.2f} reached (${SPEND['spent']:.2f} on new calls). Re-run on the next quota day; cached answers are kept.")


def classify_api_error(e: Exception) -> str | None:
    msg = str(e).lower()
    if "expired" in msg or ("401" in msg and "unauthor" in msg):
        return "Model-proxy key expired. Refresh it in a separate PowerShell window with `kaggle b auth -y`, then re-run (cached answers are kept)."
    if "exceeds your available quota" in msg or ("403" in msg and "quota" in msg):
        return "Proxy refused for quota (403). Either the daily $10 is used up or too many requests are in flight; wait / lower --workers, then re-run."
    return None


# --------------------------------------------------------------------------- cache


def cache_path(model: str, split: str, item_id: str, arm: str) -> Path:
    return CACHE / slug(model) / split / f"{item_id}__{arm}__{arm_fingerprint(arm)}.json"


def read_cache(path: Path, retry_format_errors: bool = False) -> dict | None:
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    if retry_format_errors and rec["status"] == "format_error":
        return None
    return rec


def write_cache(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def log_api_error(model: str, split: str, item_id: str, arm: str, e: Exception) -> None:
    out = RESULTS / split / f"{slug(model)}.api_errors.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    line = dict(
        time=datetime.datetime.now().isoformat(timespec="seconds"),
        item_id=item_id,
        arm=arm,
        error=f"{type(e).__name__}: {str(e)[:500]}",
    )
    with _lock, open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


# --------------------------------------------------------------------------- one call


def _last_reply(llm) -> object | None:
    for m in reversed(kbench.chats.get_current_chat().messages):
        if m.sender is llm:
            return m
    return None


def _turn_record(msg, parsed) -> dict:
    meta = msg._meta if msg is not None else {}
    reasoning = meta.get("reasoning_traces")
    return dict(
        parsed=parsed,
        raw=meta.get("raw_content"),
        input_tokens=meta.get("input_tokens"),
        output_tokens=meta.get("output_tokens"),
        cost_nanodollars=(meta.get("input_tokens_cost_nanodollars") or 0)
        + (meta.get("output_tokens_cost_nanodollars") or 0),
        latency_ms=meta.get("total_backend_latency_ms"),
        reasoning_chars=len(reasoning) if reasoning else 0,
    )


def run_arm(llm, model: str, split: str, item_id: str, image_path: str, arm: str, retry_format_errors: bool) -> dict:
    path = cache_path(model, split, item_id, arm)
    cached = read_cache(path, retry_format_errors)
    if cached is not None:
        return cached
    if ABORT.is_set():
        raise FatalRunError(ABORT_REASON[0] if ABORT_REASON else "aborted")

    mt = max_tokens_for(model)
    img = images.from_path(str(DATA / split / image_path))
    turns, status, error = [], "ok", None
    for text, schema, send_image in ARMS[arm]:
        try:
            ans = llm.prompt(
                text,
                schema=schema,
                image=img if send_image else None,
                extra_api_params={"max_tokens": mt},
            )
            turns.append(_turn_record(_last_reply(llm), ans.model_dump()))
        except FORMAT_ERRORS as e:
            turn = _turn_record(_last_reply(llm), None)
            if getattr(e, "value", None) is not None:
                turn["raw"] = e.value
            turns.append(turn)
            status, error = "format_error", f"{type(e).__name__}: {str(e)[:1500]}"
            break
        except Exception as e:
            log_api_error(model, split, item_id, arm, e)
            fatal = classify_api_error(e)
            if fatal:
                _abort(fatal)
                raise FatalRunError(fatal) from e
            raise  # transient: kbench marks the run ERRORED and retries it; nothing is cached

    rec = dict(
        model=model,
        split=split,
        item_id=item_id,
        arm=arm,
        fingerprint=arm_fingerprint(arm),
        status=status,
        error=error,
        turns=turns,
        max_tokens=mt,
        time=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    write_cache(path, rec)
    _add_spend(turns)
    return rec


RUN_CONTEXT: dict = {}


@kbench.task(name="erased_total_item", store_task=False)
def erased_total_item(llm, item_id: str, image_path: str, arm: str, fp: str) -> dict:
    """One image x one prompt arm. `fp` (arm fingerprint) keeps kbench's run cache honest."""
    rec = run_arm(
        llm,
        RUN_CONTEXT["model"],
        RUN_CONTEXT["split"],
        item_id,
        image_path,
        arm,
        RUN_CONTEXT["retry_format_errors"],
    )
    return {"status": rec["status"]}


# --------------------------------------------------------------------------- mocks


class MockLLM(LLMChat):
    """Offline stand-in. `oracle` answers from ground truth; `chaos` answers at random and
    injects transient API errors (first attempt only) and malformed output."""

    def __init__(self, policy: str, manifest: pd.DataFrame):
        super().__init__(name=f"mock/{policy}", support_structured_outputs=False)
        self.model = f"mock/{policy}"
        self.policy = policy
        self.by_sha = {r.image_sha256: r for r in manifest.itertuples()}
        self.seen: set[str] = set()

    def _row_and_text(self, messages):
        row, text = None, ""
        for m in messages:
            c = m.content
            if hasattr(c, "b64_string"):
                row = self.by_sha.get(hashlib.sha256(base64.b64decode(c.b64_string)).hexdigest())
            elif isinstance(c, str) and m.sender is kbench.actors.user:
                text = c
        return row, text

    def invoke(self, messages, system, **kwargs):
        row, text = self._row_and_text(messages)
        key = hashlib.sha256(f"{row.item_id if row else ''}|{text}|{len(messages)}".encode()).hexdigest()
        r = int(key[:8], 16) % 100
        if self.policy == "chaos":
            with _lock:
                first = key not in self.seen
                self.seen.add(key)
            if r < 6 and first:
                raise ConnectionError("mock transient API error")
            if 6 <= r < 10:
                return LLMResponse(content="Sure! The total looks like about 12 dollars.")
        if '"line_sum"' in text:
            body = {"line_sum": row.total if self.policy == "oracle" else f"{r * 3.17:.2f}", "confidence": 90}
        elif '"total_fully_visible"' in text:
            if self.policy == "oracle":
                body = {
                    "total_fully_visible": bool(row.total_visible),
                    "total_computable_from_visible_amounts": row.twin != "N",
                }
            else:
                body = {"total_fully_visible": r % 2 == 0, "total_computable_from_visible_amounts": r % 3 == 0}
        else:
            if self.policy == "oracle":
                body = {"total": row.gt, "confidence": 95 if row.gt != "UNREADABLE" else 10}
            else:
                choices = ["UNREADABLE", f"{r * 13.07:.2f}", f"covered, maybe {r * 2.5:.2f}", f"${row.total_text}", "N/A"]
                body = {"total": choices[r % len(choices)], "confidence": (r * 7) % 101}
        return LLMResponse(content=json.dumps(body), meta={"input_tokens": 1000, "output_tokens": 30})


# --------------------------------------------------------------------------- driver


def build_frame(split: str, arms: list[str], limit: int | None, coverage: str | None = None) -> pd.DataFrame:
    manifest = pd.read_csv(DATA / split / "manifest.csv", dtype={"gt": str, "total": str})
    cov = COVERAGE[coverage or split]
    rows = []
    for arm in arms:
        conds = cov.get(arm, None) if arm in cov else []
        sub = manifest if conds is None else manifest[manifest.condition.isin(conds)]
        for r in sub.itertuples():
            rows.append(dict(item_id=r.item_id, image_path=r.image_path, arm=arm, fp=arm_fingerprint(arm)))
    df = pd.DataFrame(rows)
    if limit:
        df = df.groupby("arm", sort=False).head(limit)
    return df


def label_rows(df: pd.DataFrame, model: str, split: str, retry_format_errors: bool) -> pd.DataFrame:
    """kbench caches run files by index label + model. Make the label prompt- and budget-specific,
    and fresh for rows being retried, so kbench never skips a row our own cache wants re-run."""
    mt = max_tokens_for(model)
    stamp = int(time.time())
    labels = []
    for r in df.itertuples():
        label = f"{r.item_id}__{r.arm}__{r.fp}__mt{mt}"
        if retry_format_errors:
            rec = read_cache(cache_path(model, split, r.item_id, r.arm))
            if rec is not None and rec["status"] == "format_error":
                label += f"__retry{stamp}"
        labels.append(label)
    df.index = labels
    return df


def collect(model: str, split: str, df: pd.DataFrame) -> list[dict]:
    out = []
    for r in df.itertuples():
        rec = read_cache(cache_path(model, split, r.item_id, r.arm))
        out.append(rec if rec is not None else dict(model=model, split=split, item_id=r.item_id, arm=r.arm, status="api_error", turns=[]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--arms", default="BASE,PERMIT,PROBE,TWOPASS,SUMCAP")
    ap.add_argument("--limit", type=int, default=None, help="max rows per arm (for smoke tests)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rounds", type=int, default=4, help="outer retry rounds around evaluate()")
    ap.add_argument("--retry-format-errors", action="store_true")
    ap.add_argument("--max-spend", type=float, default=None, help="stop new calls once this many dollars are spent in this run")
    ap.add_argument("--coverage", default=None, help="arm x condition table from bench.prompts.COVERAGE (default: the split's own)")
    args = ap.parse_args()
    SPEND["cap"] = args.max_spend

    arms = [a for a in args.arms.split(",") if a]
    df = label_rows(build_frame(args.split, arms, args.limit, args.coverage), args.model, args.split, args.retry_format_errors)
    manifest =pd.read_csv(DATA / args.split / "manifest.csv", dtype={"gt": str, "total": str})

    if args.model.startswith("mock/"):
        llm = MockLLM(args.model.split("/", 1)[1], manifest)
    else:
        if args.model not in kbench.llms:
            sys.exit(f"Model {args.model!r} not available. Available: {list(kbench.llms)}")
        llm = kbench.llms[args.model]
    assert args.workers <= 4, "Quota safety: at most 4 parallel requests (lesson 2)."

    RUN_CONTEXT.update(model=args.model, split=args.split, retry_format_errors=args.retry_format_errors)
    run_dir = REPO / "kbench_runs" / args.split / slug(args.model)
    run_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(kbench.client, "directory"):
        kbench.client.directory = run_dir

    todo = lambda: sum(read_cache(cache_path(args.model, args.split, r.item_id, r.arm), args.retry_format_errors) is None for r in df.itertuples())
    print(f"{args.model} | split={args.split} | arms={arms} | rows={len(df)} | uncached={todo()} | max_tokens={max_tokens_for(args.model)}")

    t0 = time.time()
    for rnd in range(1, args.rounds + 1):
        if todo() == 0 or ABORT.is_set():
            break
        try:
            with kbench.client.enable_cache():
                erased_total_item.evaluate(
                    llm=[llm],
                    evaluation_data=df,
                    n_jobs=args.workers,
                    timeout=300,
                    on_failure="continue",
                    max_attempts=3,
                    retry_delay=10,
                    stop_condition=lambda _runs: ABORT.is_set(),
                )
        except Exception as e:  # e.g. a TimeoutError for a whole batch; cached answers make retries cheap
            print(f"round {rnd}: evaluate() raised {type(e).__name__}: {str(e)[:300]}")
            traceback.print_exc(limit=2)
            time.sleep(5)
        print(f"round {rnd} done: uncached={todo()} ({time.time() - t0:.0f}s)")

    recs = collect(args.model, args.split, df)
    out = RESULTS / args.split / f"{slug(args.model)}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for rec in recs:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    status = pd.Series([r["status"] for r in recs]).value_counts().to_dict()
    cost = sum(t.get("cost_nanodollars") or 0 for r in recs for t in r.get("turns", [])) / 1e9
    print(f"wrote {out.relative_to(REPO)} | status={status} | logged cost ${cost:.4f} | new spend this run ${SPEND['spent']:.4f}")
    if ABORT.is_set():
        print("STOPPED:", ABORT_REASON[0])
        sys.exit(2)


if __name__ == "__main__":
    main()
