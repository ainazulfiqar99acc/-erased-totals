"""Deterministic scoring (preregistration §5). No LLM judge."""

from __future__ import annotations

import math
import re

import numpy as np
import pandas as pd

ABSTAIN_RE = re.compile(
    r"unreadable|illegible|unclear|obscur|cover|hidden|redact|occlu|mask|blocked|missing"
    r"|cannot|can't|can not|unable|unknown|undetermin|indetermin|not\s+determin"
    r"|not\s+(?:fully\s+|clearly\s+)?(?:visible|legible|readable|shown|available|known|provided)"
    r"|\bn/?a\b|\bnone\b|\bnull\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


def parse_number(text: str) -> float | None:
    m = NUMBER_RE.search(text)
    return float(m.group(0).replace(",", "")) if m else None


# Real-scan add-on (CORD, Indonesian rupiah): "45.500" and "45,500" both mean 45500, and a
# trailing 1–2 digit group after a different separator is decimals ("45.500,00", "45,500.00").
IDR_TOKEN_RE = re.compile(r"\d[\d.,]*\d|\d")


def parse_number_idr(text: str) -> float | None:
    m = IDR_TOKEN_RE.search(text)
    if not m:
        return None
    tok = m.group(0)
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", tok) and len(set(re.sub(r"\d", "", tok))) == 1:
        return float(re.sub(r"[.,]", "", tok))
    d = re.fullmatch(r"(\d{1,3}(?:([.,])\d{3})*|\d+)([.,])(\d{1,2})", tok)
    if d and d.group(2) != d.group(3):
        return float(re.sub(r"[.,]", "", d.group(1)) + "." + d.group(4))
    if tok.isdigit():
        return float(tok)
    return parse_number(text)


def classify(answer, money: str = "default") -> tuple[str, float | None]:
    """Returns (abstain | hedged_number | number, parsed value)."""
    if answer is None:
        return "abstain", None
    s = str(answer).strip()
    value = parse_number_idr(s) if money == "idr" else parse_number(s)
    if value is None:
        return "abstain", None
    if ABSTAIN_RE.search(s):
        return "hedged_number", value
    return "number", value


def norm_confidence(c) -> float | None:
    if c is None or (isinstance(c, float) and math.isnan(c)):
        return None
    c = float(c)
    if c <= 1.0:
        c *= 100
    return min(100.0, max(0.0, c))


def score_answer(gt: str, answer, money: str = "default") -> dict:
    """Score one total/sum answer against ground truth ("1234.56" or "UNREADABLE")."""
    kind, value = classify(answer, money)
    if gt == "UNREADABLE":
        correct = kind == "abstain"
        return dict(
            answer_kind=kind,
            answer_value=value,
            correct=correct,
            invention=kind == "number",
            invention_lenient=kind in ("number", "hedged_number"),
        )
    correct = kind == "number" and abs(value - float(gt)) < 0.005
    return dict(
        answer_kind=kind,
        answer_value=value,
        correct=correct,
        invention=None,
        invention_lenient=None,
    )


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def brier(conf: pd.Series, correct: pd.Series) -> float:
    m = conf.notna()
    if not m.any():
        return math.nan
    return float(((conf[m] / 100 - correct[m].astype(float)) ** 2).mean())


def ece(conf: pd.Series, correct: pd.Series, bins: int = 10) -> float:
    m = conf.notna()
    if not m.any():
        return math.nan
    p = (conf[m] / 100).to_numpy()
    y = correct[m].astype(float).to_numpy()
    idx = np.minimum((p * bins).astype(int), bins - 1)
    total = 0.0
    for b in range(bins):
        sel = idx == b
        if sel.any():
            total += sel.sum() / len(p) * abs(p[sel].mean() - y[sel].mean())
    return float(total)


def bootstrap_ci(df: pd.DataFrame, stat, cluster: str = "bill_id", n: int = 10_000, seed: int = 0):
    """Cluster bootstrap over bills: 95% percentile interval of stat(df)."""
    rng = np.random.default_rng(seed)
    groups = {k: g for k, g in df.groupby(cluster)}
    keys = list(groups)
    vals = []
    for _ in range(n):
        sample = rng.choice(keys, size=len(keys), replace=True)
        vals.append(stat(pd.concat([groups[k] for k in sample])))
    return tuple(np.nanpercentile(vals, [2.5, 97.5]))
