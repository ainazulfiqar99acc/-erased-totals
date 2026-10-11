"""Seeded renderer for synthetic bills with exact ground truth.

Every amount is an integer number of cents and the page is drawn from those values, so
labels are exact by construction. Each bill is laid out once (clean page plus the pixel
boxes of the fields we occlude); occluders are then drawn per condition, and the same
photo degradation (same seed) is applied to every condition of that bill, so twin images
differ only in where the tape sits.

No other route to the total exists on the page: no subtotal, no tax rate, no unit price,
no amount in words, no amount paid / change, no barcode.

Usage:
    python -m bench.render --split pilot
    python -m bench.render --split main
    python -m bench.render --split smoke
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime
import hashlib
import io
import json
import math
import os
import platform
import random
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RENDERER_VERSION = "1.0.0"
REPO = Path(__file__).resolve().parent.parent
FONT_DIR = Path(os.environ.get("BENCH_FONT_DIR", r"C:\Windows\Fonts"))

ALL_CONDITIONS = ["clean", "D0", "D25", "D50", "D75", "D100", "N0", "N25", "N50", "N75", "N100"]
PILOT_CONDITIONS = ["clean", "D0", "D50", "D100", "N50", "N100"]

# split -> (seed base, number of bills, conditions)
SPLITS = {
    "smoke": (9000, 1, ["clean"]),
    "pilot": (1000, 12, PILOT_CONDITIONS),
    "main": (2000, 48, ALL_CONDITIONS),
}

DOC_TYPES = [
    "retail_receipt",
    "restaurant_bill",
    "utility_bill",
    "service_invoice",
    "lab_invoice",
    "fee_statement",
]
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "CHF"]

ISSUER_FIRST = [
    "Northgate", "Bluefield", "Harbor Lane", "Cedar Point", "Maple Row", "Silver Oak",
    "Greenway", "Stonebridge", "Brightwater", "Westfield", "Elm Street", "Hillcrest",
    "Lakeside", "Sunridge", "Fairview", "Kingsley", "Ashford", "Copperfield",
]
STREETS = [
    "Station Road", "Market Street", "Mill Lane", "Park Avenue", "Church Road",
    "Bridge Street", "High Street", "Garden Way", "Orchard Close", "Quarry Road",
]
SURNAMES = [
    "Rivera", "Chen", "Okafor", "Novak", "Haddad", "Silva", "Kim", "Andersen", "Mensah",
    "Kowalski", "Tanaka", "Morgan", "Rossi", "Dubois", "Kaur", "Ibrahim", "Larsen", "Costa",
]
INITIALS = "ABCDEFGHJKLMNPRSTW"

SPECS = {
    "retail_receipt": dict(
        style="receipt",
        title="SALES RECEIPT",
        issuer_second=["Market", "Grocers", "General Store", "Mart", "Supplies"],
        number_label="Receipt No",
        total_labels=["TOTAL", "TOTAL DUE"],
        qty=True,
        items=[
            "Notebook A5", "Ballpoint pens (10)", "Coffee beans 250g", "Olive oil 1L",
            "Dish soap", "Paper towels", "AA batteries (4)", "Rice 2kg", "Tomatoes",
            "Bread loaf", "Cheddar cheese", "Shampoo", "Toothpaste", "USB cable",
            "LED light bulb", "Apples 1kg", "Milk 1L", "Eggs (12)", "Laundry detergent",
            "Tea bags (50)",
        ],
        cents=(80, 6000),
        footer=["Thank you for shopping with us!", "Please keep this receipt for returns."],
    ),
    "restaurant_bill": dict(
        style="receipt",
        title="GUEST BILL",
        issuer_second=["Bistro", "Kitchen", "Cafe", "Grill", "Diner"],
        number_label="Bill No",
        total_labels=["TOTAL", "AMOUNT DUE"],
        qty=True,
        items=[
            "Grilled chicken", "Caesar salad", "Margherita pizza", "Pasta arrabbiata",
            "Lemonade", "Sparkling water", "Espresso", "Cheesecake", "Tomato soup",
            "Fish tacos", "Veggie burger", "Fries", "Iced tea", "Garlic bread", "Fruit bowl",
        ],
        cents=(250, 4500),
        fee=("Service charge", (200, 1500)),
        footer=["Thank you for dining with us!", "We hope to see you again soon."],
    ),
    "utility_bill": dict(
        style="invoice",
        title="ELECTRICITY BILL",
        issuer_second=["Power & Light", "Energy", "Utilities", "Electric", "Water & Power"],
        number_label="Account No",
        total_labels=["TOTAL AMOUNT DUE", "AMOUNT PAYABLE"],
        qty=False,
        items=[
            "Energy charge", "Fixed monthly charge", "Meter service fee", "Network charge",
            "Environmental levy", "Sales tax", "Previous balance", "Street lighting levy",
        ],
        cents=(500, 15000),
        extra_fields=[("Billing period", "period"), ("Due date", "due")],
        footer=["Please pay by the due date shown above.", "Questions about this bill? Call 555-0199."],
    ),
    "service_invoice": dict(
        style="invoice",
        title="INVOICE",
        issuer_second=["Consulting", "Technical Services", "Solutions", "Systems", "Partners"],
        number_label="Invoice No",
        total_labels=["TOTAL", "BALANCE DUE"],
        qty=True,
        items=[
            "Consulting hours", "Site visit", "Software licence (annual)", "Equipment rental",
            "Installation", "Training session", "Travel expenses", "Maintenance plan",
            "Data migration", "Support hours",
        ],
        cents=(5000, 120000),
        extra_fields=[("Due date", "due")],
        footer=["Payment terms: 30 days.", "Thank you for your business."],
    ),
    "lab_invoice": dict(
        style="invoice",
        title="PATIENT INVOICE",
        issuer_second=["Diagnostics", "Medical Laboratory", "Clinical Lab", "Health Labs", "Pathology"],
        number_label="Invoice No",
        total_labels=["TOTAL", "TOTAL PAYABLE"],
        qty=False,
        items=[
            "Complete blood count", "Lipid panel", "Thyroid function test", "Vitamin D test",
            "Urinalysis", "Chest X-ray", "Consultation fee", "Sample collection fee",
            "Blood glucose (fasting)", "Liver function test", "ECG",
        ],
        cents=(1500, 25000),
        extra_fields=[("Patient ID", "pid")],
        footer=["Results are available online within 48 hours.", "Please bring this invoice to the reception desk."],
    ),
    "fee_statement": dict(
        style="invoice",
        title="FEE STATEMENT",
        issuer_second=["Academy", "College", "School", "Institute", "Learning Centre"],
        number_label="Statement No",
        total_labels=["TOTAL FEES DUE", "TOTAL PAYABLE"],
        qty=False,
        items=[
            "Tuition fee", "Library fee", "Laboratory fee", "Examination fee", "Sports fee",
            "Technology fee", "Transport fee", "Activity fee", "Registration fee",
        ],
        cents=(2000, 150000),
        extra_fields=[("Student ID", "sid"), ("Term", "term"), ("Due date", "due")],
        footer=["Fees are payable at the accounts office or by bank transfer.", "Please quote your student ID with every payment."],
    ),
}

RECEIPT_FONTS = [("consola.ttf", "consolab.ttf"), ("cour.ttf", "courbd.ttf")]
INVOICE_FONTS = [
    ("arial.ttf", "arialbd.ttf"), ("calibri.ttf", "calibrib.ttf"), ("verdana.ttf", "verdanab.ttf"),
    ("segoeui.ttf", "segoeuib.ttf"), ("tahoma.ttf", "tahomabd.ttf"), ("georgia.ttf", "georgiab.ttf"),
]

INK = (28, 28, 32)
TAPE_FILL = (196, 196, 192)
TAPE_EDGE = (150, 150, 146)
MAX_LONG_EDGE = 1100
JPEG_QUALITY = 85


def fmt_amount(cents: int) -> str:
    return f"{cents // 100:,}.{cents % 100:02d}"


def gt_string(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


@dataclasses.dataclass
class Line:
    desc: str
    qty: int | None
    cents: int


@dataclasses.dataclass
class Bill:
    split: str
    bill_id: str
    seed: int
    doc_type: str
    currency: str
    issuer: str
    address: str
    phone: str
    title: str
    number_label: str
    doc_no: str
    date: str
    customer: str
    extra_fields: list[tuple[str, str]]
    lines: list[Line]
    total_label: str
    total_cents: int
    cover_side: str  # "lead" (leading characters covered first) or "trail"
    hidden_line: int  # index of the amount line covered in the N twin
    font_regular: str
    font_bold: str
    paper: tuple[int, int, int]
    photo: dict


def _date(rng: random.Random) -> datetime.date:
    start = datetime.date(2025, 1, 1)
    return start + datetime.timedelta(days=rng.randrange(0, 638))


def _fmt_date(d: datetime.date, style: int) -> str:
    return d.isoformat() if style == 0 else d.strftime("%d %b %Y")


def make_bill(split: str, index: int, seed: int) -> Bill:
    rng = random.Random(seed)
    doc_type = DOC_TYPES[index % len(DOC_TYPES)]
    spec = SPECS[doc_type]
    cover_side = "lead" if (index // len(DOC_TYPES)) % 2 == 0 else "trail"

    n_lines = rng.randint(3, 7)
    descs = rng.sample(spec["items"], min(n_lines, len(spec["items"])))
    lines = []
    for d in descs:
        qty = rng.choice([1, 1, 1, 2, 2, 3, 4]) if spec["qty"] else None
        lines.append(Line(d, qty, rng.randint(*spec["cents"])))
    if "fee" in spec and rng.random() < 0.5:
        lines[-1] = Line(spec["fee"][0], None, rng.randint(*spec["fee"][1]))
    total = sum(l.cents for l in lines)

    d = _date(rng)
    date_style = rng.randint(0, 1)
    extra = []
    for label, kind in spec.get("extra_fields", []):
        if kind == "due":
            value = _fmt_date(d + datetime.timedelta(days=rng.choice([14, 21, 30])), date_style)
        elif kind == "period":
            p0 = d - datetime.timedelta(days=30)
            value = f"{_fmt_date(p0, date_style)} to {_fmt_date(d, date_style)}"
        elif kind == "pid":
            value = f"P-{rng.randint(100000, 999999)}"
        elif kind == "sid":
            value = f"S{rng.randint(10000, 99999)}"
        elif kind == "term":
            value = rng.choice(["Autumn", "Spring", "Summer"]) + f" {d.year}"
        else:
            raise ValueError(kind)
        extra.append((label, value))

    if spec["number_label"] == "Account No":
        doc_no = f"{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}-{rng.randint(10, 99)}"
    elif spec["style"] == "receipt":
        doc_no = f"{rng.randint(0, 999999):06d}"
    else:
        doc_no = f"{d.year}-{rng.randint(1000, 99999):05d}"

    fonts = rng.choice(RECEIPT_FONTS if spec["style"] == "receipt" else INVOICE_FONTS)
    tint = rng.randint(0, 8)
    bg = rng.choice([(92, 74, 58), (120, 120, 118), (60, 64, 70), (150, 132, 108)])
    return Bill(
        split=split,
        bill_id=f"b{index:02d}",
        seed=seed,
        doc_type=doc_type,
        currency=rng.choice(CURRENCIES),
        issuer=f"{rng.choice(ISSUER_FIRST)} {rng.choice(spec['issuer_second'])}",
        address=f"{rng.randint(2, 240)} {rng.choice(STREETS)}",
        phone=f"Tel 555-01{rng.randint(10, 99)}",
        title=spec["title"],
        number_label=spec["number_label"],
        doc_no=doc_no,
        date=_fmt_date(d, date_style) + (f"  {rng.randint(8, 21):02d}:{rng.randint(0, 59):02d}" if spec["style"] == "receipt" else ""),
        customer=f"{rng.choice(INITIALS)}. {rng.choice(SURNAMES)}",
        extra_fields=extra,
        lines=lines,
        total_label=rng.choice(spec["total_labels"]),
        total_cents=total,
        cover_side=cover_side,
        hidden_line=rng.randrange(len(lines)),
        font_regular=fonts[0],
        font_bold=fonts[1],
        paper=(250 - tint, 248 - tint, 242 - tint),
        photo=dict(
            angle=round(rng.uniform(-1.5, 1.5), 3),
            blur=0.4,
            margin=rng.randint(30, 44),
            bg=bg,
        ),
    )


@dataclasses.dataclass
class Field:
    text: str
    bbox: tuple[float, float, float, float]
    char_boxes: list[tuple[float, float, float, float]]


class Canvas:
    def __init__(self, width: int, paper, regular: str, bold: str):
        self.width = width
        self.img = Image.new("RGB", (width, 2400), paper)
        self.draw = ImageDraw.Draw(self.img)
        self._fonts = {}
        self.regular_path = FONT_DIR / regular
        self.bold_path = FONT_DIR / bold

    def font(self, size: int, bold: bool = False):
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(str(self.bold_path if bold else self.regular_path), size)
        return self._fonts[key]

    def text(self, x, y, s, size, bold=False, align="left", fill=INK) -> Field:
        f = self.font(size, bold)
        w = self.draw.textlength(s, font=f)
        if align == "right":
            x = x - w
        elif align == "center":
            x = x - w / 2
        self.draw.text((x, y), s, font=f, fill=fill)
        boxes = [
            self.draw.textbbox((x + self.draw.textlength(s[:i], font=f), y), ch, font=f)
            for i, ch in enumerate(s)
        ]
        return Field(s, self.draw.textbbox((x, y), s, font=f), boxes)

    def hline(self, y, x0, x1, width=1, dashed=False):
        if not dashed:
            self.draw.line([(x0, y), (x1, y)], fill=INK, width=width)
            return
        x = x0
        while x < x1:
            self.draw.line([(x, y), (min(x + 8, x1), y)], fill=INK, width=width)
            x += 14


def layout_receipt(bill: Bill):
    c = Canvas(540, bill.paper, bill.font_regular, bill.font_bold)
    m, W = 30, 540
    y = 34
    c.text(W / 2, y, bill.issuer.upper(), 26, bold=True, align="center"); y += 40
    c.text(W / 2, y, bill.address, 18, align="center"); y += 26
    c.text(W / 2, y, bill.phone, 18, align="center"); y += 44
    c.text(W / 2, y, bill.title, 22, bold=True, align="center"); y += 40
    lab = c.text(m, y, f"{bill.number_label}: ", 19)
    decoy = c.text(lab.bbox[2] + 2, y, bill.doc_no, 19); y += 28
    c.text(m, y, f"Date: {bill.date}", 19); y += 28
    if bill.doc_type == "restaurant_bill":
        c.text(m, y, f"Table: {1 + bill.seed % 24}   Server: {10 + bill.seed % 40}", 19); y += 28
    else:
        c.text(m, y, f"Cashier: {10 + bill.seed % 40}", 19); y += 28
    y += 10; c.hline(y, m, W - m, dashed=True); y += 14
    c.text(m, y, "QTY", 18, bold=True)
    c.text(m + 60, y, "ITEM", 18, bold=True)
    c.text(W - m, y, f"AMOUNT ({bill.currency})", 18, bold=True, align="right"); y += 32
    amounts = []
    for line in bill.lines:
        if line.qty is not None:
            c.text(m + 8, y, str(line.qty), 20)
        c.text(m + 60, y, line.desc, 20)
        amounts.append(c.text(W - m, y, fmt_amount(line.cents), 20, align="right"))
        y += 32
    y += 4; c.hline(y, m, W - m, dashed=True); y += 16
    c.text(m, y, bill.total_label, 24, bold=True)
    total = c.text(W - m, y, fmt_amount(bill.total_cents), 24, bold=True, align="right"); y += 40
    c.hline(y, m, W - m, dashed=True); y += 24
    for s in SPECS[bill.doc_type]["footer"]:
        c.text(W / 2, y, s, 17, align="center"); y += 26
    y += 24
    return c.img.crop((0, 0, W, int(y))), total, amounts, decoy


def layout_invoice(bill: Bill):
    W = 820
    c = Canvas(W, bill.paper, bill.font_regular, bill.font_bold)
    m = 50
    y = 44
    c.text(m, y, bill.issuer, 30, bold=True)
    c.text(W - m, y + 4, bill.title, 24, bold=True, align="right"); y += 46
    c.text(m, y, bill.address, 17); y += 24
    c.text(m, y, bill.phone, 17); y += 44

    left_y, right_y = y, y
    c.text(m, left_y, "Billed to:", 18, bold=True); left_y += 28
    c.text(m, left_y, bill.customer, 18); left_y += 28
    rx = W // 2 + 30
    lab = c.text(rx, right_y, f"{bill.number_label}: ", 18)
    decoy = c.text(lab.bbox[2] + 2, right_y, bill.doc_no, 18); right_y += 28
    c.text(rx, right_y, f"Date: {bill.date}", 18); right_y += 28
    for label, value in bill.extra_fields:
        c.text(rx, right_y, f"{label}: {value}", 18); right_y += 28
    y = max(left_y, right_y) + 26

    has_qty = any(l.qty is not None for l in bill.lines)
    c.draw.rectangle([m, y - 6, W - m, y + 30], fill=(228, 228, 224))
    c.text(m + 10, y, "Description", 18, bold=True)
    if has_qty:
        c.text(W - m - 230, y, "Qty", 18, bold=True, align="right")
    c.text(W - m - 10, y, f"Amount ({bill.currency})", 18, bold=True, align="right"); y += 46
    amounts = []
    for line in bill.lines:
        c.text(m + 10, y, line.desc, 19)
        if line.qty is not None:
            c.text(W - m - 230, y, str(line.qty), 19, align="right")
        amounts.append(c.text(W - m - 10, y, fmt_amount(line.cents), 19, align="right"))
        y += 34
        c.hline(y - 7, m, W - m, width=1)
    y += 14
    c.hline(y - 6, W // 2, W - m, width=2)
    c.text(W // 2 + 10, y + 4, bill.total_label, 21, bold=True)
    total = c.text(W - m - 10, y + 4, fmt_amount(bill.total_cents), 22, bold=True, align="right")
    y += 48
    c.hline(y - 6, W // 2, W - m, width=2); y += 40
    for s in SPECS[bill.doc_type]["footer"]:
        c.text(m, y, s, 17); y += 26
    y += 34
    return c.img.crop((0, 0, W, int(y))), total, amounts, decoy


def layout(bill: Bill):
    if SPECS[bill.doc_type]["style"] == "receipt":
        return layout_receipt(bill)
    return layout_invoice(bill)


def n_covered(dose: float, n_chars: int) -> int:
    return max(1, math.floor(dose * n_chars + 0.5))


def total_tape(total: Field, dose: float, side: str, pad: int = 5):
    """Box covering whole characters of the total value; returns (box, visible fragment)."""
    l, t, r, b = total.bbox
    y0, y1 = t - pad, b + pad
    n = len(total.text)
    if dose >= 1.0:
        return (l - pad, y0, r + pad, y1), ""
    k = n_covered(dose, n)
    cb = total.char_boxes
    if side == "lead":
        x_end = (cb[k - 1][2] + cb[k][0]) / 2
        return (l - pad, y0, x_end, y1), total.text[k:]
    x_start = (cb[n - k - 1][2] + cb[n - k][0]) / 2
    return (x_start, y0, r + pad, y1), total.text[: n - k]


def field_tape(f: Field, pad: int = 5):
    l, t, r, b = f.bbox
    return (l - pad, t - pad, r + pad, b + pad)


def apply_tape(img: Image.Image, boxes) -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    for box in boxes:
        d.rectangle([round(v) for v in box], fill=TAPE_FILL, outline=TAPE_EDGE, width=2)
    return out


def photograph(page: Image.Image, photo: dict) -> bytes:
    m = photo["margin"]
    bg = tuple(photo["bg"])
    canvas = Image.new("RGB", (page.width + 2 * m, page.height + 2 * m), bg)
    canvas.paste(page, (m, m))
    canvas = canvas.rotate(photo["angle"], resample=Image.BICUBIC, expand=False, fillcolor=bg)
    canvas = canvas.filter(ImageFilter.GaussianBlur(photo["blur"]))
    scale = min(1.0, MAX_LONG_EDGE / max(canvas.size))
    if scale < 1.0:
        canvas = canvas.resize((round(canvas.width * scale), round(canvas.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def condition_spec(cond: str) -> tuple[str, float]:
    if cond == "clean":
        return "clean", 0.0
    return cond[0], int(cond[1:]) / 100


def render_split(split: str, out_root: Path) -> dict:
    seed_base, n_bills, conditions = SPLITS[split]
    out = out_root / split
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    bills, rows = [], []
    for i in range(n_bills):
        bill = make_bill(split, i, seed_base + i)
        page, total, amounts, decoy = layout(bill)
        bills.append(dataclasses.asdict(bill))
        for cond in conditions:
            twin, dose = condition_spec(cond)
            boxes, fragment = [], fmt_amount(bill.total_cents)
            if dose > 0:
                box, fragment = total_tape(total, dose, bill.cover_side)
                boxes.append(box)
            if twin == "D":
                boxes.append(field_tape(decoy))
            elif twin == "N":
                boxes.append(field_tape(amounts[bill.hidden_line]))
            jpg = photograph(apply_tape(page, boxes), bill.photo)
            item_id = f"{split}_{bill.bill_id}_{cond}"
            path = img_dir / f"{item_id}.jpg"
            path.write_bytes(jpg)
            derivable = twin != "N" or dose == 0
            rows.append(
                dict(
                    item_id=item_id,
                    split=split,
                    bill_id=bill.bill_id,
                    doc_type=bill.doc_type,
                    condition=cond,
                    twin=twin,
                    dose=dose,
                    cover_side=bill.cover_side if dose > 0 else "",
                    total_visible=dose == 0,
                    derivable=derivable,
                    gt=gt_string(bill.total_cents) if derivable else "UNREADABLE",
                    total=gt_string(bill.total_cents),
                    total_text=fmt_amount(bill.total_cents),
                    visible_fragment=fragment if 0 < dose < 1 else "",
                    n_lines=len(bill.lines),
                    hidden_line=bill.hidden_line if twin == "N" else "",
                    hidden_line_amount=gt_string(bill.lines[bill.hidden_line].cents) if twin == "N" else "",
                    image_path=f"images/{path.name}",
                    image_sha256=hashlib.sha256(jpg).hexdigest(),
                )
            )

    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "bills.json").write_text(json.dumps(bills, indent=1), encoding="utf-8")

    fonts = sorted({b["font_regular"] for b in bills} | {b["font_bold"] for b in bills})
    meta = dict(
        renderer_version=RENDERER_VERSION,
        split=split,
        seed_base=seed_base,
        n_bills=n_bills,
        conditions=conditions,
        n_images=len(rows),
        rendered_on=datetime.date.today().isoformat(),
        python=platform.python_version(),
        pillow=PIL.__version__,
        fonts={name: hashlib.sha256((FONT_DIR / name).read_bytes()).hexdigest() for name in fonts},
        manifest_csv_sha256=hashlib.sha256((out / "manifest.csv").read_bytes()).hexdigest(),
        bills_json_sha256=hashlib.sha256((out / "bills.json").read_bytes()).hexdigest(),
    )
    (out / "MANIFEST.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=sorted(SPLITS), required=True)
    ap.add_argument("--out", default=str(REPO / "data"))
    args = ap.parse_args()
    meta = render_split(args.split, Path(args.out))
    print(json.dumps({k: meta[k] for k in ("split", "n_bills", "n_images", "manifest_csv_sha256")}, indent=1))


if __name__ == "__main__":
    main()
