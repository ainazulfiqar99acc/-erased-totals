"""Real-scan add-on (exploratory; preregistration Deviation 5): taped totals on CORD receipts.

    python -m bench.cord

Source: CORD v2 (naver-clova-ix/cord-v2, CC-BY-4.0), pinned revision and SHA-256 below. Real
phone photos of Indonesian receipts with word boxes and field labels, so the total, the line
amounts and every other money field can be located and taped exactly, and ground truth comes
from the dataset's own labels (never hand-typed).

Per selected receipt, three images (same names as the main split so the analysis code applies):
  clean  no tape                                                      GT = total
  D100   total taped (+ any field equal to it); line amounts visible  GT = total (derivable)
  N100   D100 + every subtotal/tax/service/discount/payment amount    GT = UNREADABLE
         + one line item's amount taped
Only value words are taped (CORD `is_key == 0`); labels such as "TOTAL" stay visible.
"""

import hashlib
import io
import json
import random
import re
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from bench.scoring import parse_number_idr

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "cord_raw"
OUT = REPO / "data" / "cord"

REVISION = "7f0115a4b758a71d6473b8d085751692da2fef98"
SOURCES = {
    "test": ("test-00000-of-00001-9c204eb3f4e11791.parquet", "51c65f1788faff392abe2a0b55b023eb23e9be551c509138eaa3a832514224e7"),
    "validation": ("validation-00000-of-00001-cc3c5779fe22e8ca.parquet", "0d0f6dac11fdcc549de2746aa9f53136a3bc22a2a1aff2b0b847f7622ad60c15"),
}
N_RECEIPTS = 30
SEED = 0
MAX_EDGE = 1568
TAPE_FILL, TAPE_EDGE = (196, 196, 192), (150, 150, 146)

PAYMENT = {"total.total_price", "total.cashprice", "total.changeprice", "total.creditcardprice", "total.emoneyprice", "total.total_etc"}
LINE_MONEY = {"menu.price", "menu.unitprice", "menu.itemsubtotal", "menu.discountprice"}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def money(text: str) -> int | None:
    v = parse_number_idr(text)
    return int(round(v)) if v is not None and v == int(v) else None


def value_text(line: dict) -> str:
    return " ".join(w["text"] for w in line["words"] if not w["is_key"])


def eligible(g: dict) -> dict | None:
    """Receipt qualifies if its labelled line amounts give the total by a route the image shows.
    R1: sum(lines) == total. R2: sum(lines) + tax + service - discount == total."""
    p = g["gt_parse"]
    menu = p.get("menu", [])
    menu = menu if isinstance(menu, list) else [menu]
    st, tot = p.get("sub_total") or {}, p.get("total") or {}
    if isinstance(st, list) or isinstance(tot, list) or not tot.get("total_price"):
        return None
    if any(not isinstance(v, str) for v in list(st.values()) + [tot["total_price"]]):
        return None  # a field labelled twice: ambiguous
    if any(any(k.startswith("sub") or k == "discountprice" for k in m) for m in menu):
        return None
    if set(st) - {"subtotal_price", "tax_price", "service_price", "discount_price"}:
        return None
    total = money(tot["total_price"])
    # Line amounts from the boxed words, one menu.price line per item (group_id).
    groups: dict[int, list] = {}
    for line in g["valid_line"]:
        if line["category"] == "menu.price":
            groups.setdefault(line["group_id"], []).append(line)
    if len(groups) < 2 or any(len(v) != 1 for v in groups.values()):
        return None
    prices = {gid: money(value_text(v[0])) for gid, v in groups.items()}
    if total is None or None in prices.values() or total in prices.values() or 0 in prices.values():
        return None
    s = sum(prices.values())
    sub = money(st["subtotal_price"]) if st.get("subtotal_price") else None
    if sub is not None and sub != s:
        return None
    adj = lambda k: abs(money(st[k]) or 0) if st.get(k) else 0
    if s == total:
        route = "R1"
    elif s + adj("tax_price") + adj("service_price") - adj("discount_price") == total:
        route = "R2"
    else:
        return None
    return dict(total=total, prices=prices, route=route, subtotal=sub)


def tape_lines(img: Image.Image, lines: list[dict], sx: float, sy: float) -> None:
    d = ImageDraw.Draw(img)
    for line in lines:
        for w in line["words"]:
            if w["is_key"]:
                continue
            q = w["quad"]
            xs = [q[f"x{i}"] * sx for i in range(1, 5)]
            ys = [q[f"y{i}"] * sy for i in range(1, 5)]
            h = max(ys) - min(ys)
            pad = max(2, round(0.25 * h))
            box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
            d.rectangle(box, fill=TAPE_FILL, outline=TAPE_EDGE, width=max(1, round(h / 12)))


def build() -> None:
    candidates = []
    for split, (fname, want) in SOURCES.items():
        raw = (RAW / fname).read_bytes()
        assert sha256(raw) == want, f"{fname}: SHA-256 mismatch"
        df = pd.read_parquet(io.BytesIO(raw))
        for idx, row in df.iterrows():
            g = json.loads(row.ground_truth)
            info = eligible(g)
            if info:
                candidates.append((split, int(idx), g, row.image["bytes"], info))
    rng = random.Random(SEED)
    chosen = sorted(rng.sample(candidates, N_RECEIPTS), key=lambda c: (c[0], c[1]))

    (OUT / "images").mkdir(parents=True, exist_ok=True)
    rows, receipts = [], []
    for k, (split, idx, g, img_bytes, info) in enumerate(chosen):
        bill_id = f"r{k:02d}"
        base = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        meta = g["meta"]["image_size"]
        sx, sy = base.width / meta["width"], base.height / meta["height"]
        lines = g["valid_line"]
        vals = [(line, money(value_text(line))) for line in lines]
        total, prices = info["total"], info["prices"]

        # Hidden line for N100: an amount that appears nowhere else on the receipt.
        counts = pd.Series([v for _, v in vals if v is not None]).value_counts()
        options = sorted(gid for gid, v in prices.items() if counts.get(v, 0) == 1 and v != info["subtotal"])
        if not options:
            options = sorted(prices)
        hidden = random.Random(f"{split}-{idx}").choice(options)
        hidden_amount = prices[hidden]

        d_tape = [l for l, v in vals if l["category"] == "total.total_price" or (v == total and not l["category"].startswith("menu."))]
        n_tape = [
            l for l, v in vals
            if l["category"] in PAYMENT
            or l["category"].startswith("sub_total.")
            or (l["category"] in LINE_MONEY and l["group_id"] == hidden)
            or (v is not None and v in (total, hidden_amount, info["subtotal"]) and not l["category"].startswith("menu.cnt"))
        ]
        for cond, twin, tape in (("clean", "clean", []), ("D100", "D", d_tape), ("N100", "N", n_tape)):
            img = base.copy()
            tape_lines(img, tape, sx, sy)
            scale = min(1.0, MAX_EDGE / max(img.size))
            if scale < 1:
                img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
            item_id = f"cord_{bill_id}_{cond}"
            path = OUT / "images" / f"{item_id}.jpg"
            img.save(path, "JPEG", quality=90)
            rows.append(dict(
                item_id=item_id, split="cord", bill_id=bill_id, doc_type="cord_receipt", condition=cond, twin=twin,
                dose=0.0 if cond == "clean" else 1.0, cover_side="", total_visible=cond == "clean",
                derivable=cond != "N100", gt="UNREADABLE" if cond == "N100" else str(total), total=str(total),
                total_text=value_text(next(l for l in lines if l["category"] == "total.total_price")),
                visible_fragment="", n_lines=len(prices), hidden_line=hidden if cond == "N100" else "",
                hidden_line_amount=hidden_amount if cond == "N100" else "",
                image_path=f"images/{path.name}", image_sha256=sha256(path.read_bytes()),
            ))
        receipts.append(dict(bill_id=bill_id, source_split=split, source_index=idx, route=info["route"], total=total,
                             n_lines=len(prices), hidden_group=hidden, hidden_amount=hidden_amount,
                             d_taped=sorted({l["category"] for l in d_tape}), n_taped=sorted({l["category"] for l in n_tape})))

    manifest = pd.DataFrame(rows)
    manifest.to_csv(OUT / "manifest.csv", index=False)
    (OUT / "receipts.json").write_text(json.dumps(receipts, indent=1), encoding="utf-8")
    info = dict(
        source="naver-clova-ix/cord-v2 (CC-BY-4.0)", revision=REVISION,
        source_sha256={s: v[1] for s, v in SOURCES.items()}, n_eligible=len(candidates), n_receipts=N_RECEIPTS,
        seed=SEED, n_images=len(manifest), manifest_csv_sha256=sha256((OUT / "manifest.csv").read_bytes()),
        routes=pd.Series([r["route"] for r in receipts]).value_counts().to_dict(),
    )
    (OUT / "MANIFEST.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    build()
