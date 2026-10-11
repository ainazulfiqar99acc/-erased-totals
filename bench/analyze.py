"""Score cached results and evaluate hypotheses / validity checks / pilot gate.

    python -m bench.analyze --split pilot [--models a,b,c]

Writes results/<split>/scored.csv and results/<split>/report.md.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from bench.prompts import COVERAGE
from bench.scoring import brier, ece, norm_confidence, score_answer, wilson

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
RESULTS = REPO / "results"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(split: str, models: list[str] | None) -> pd.DataFrame:
    manifest = pd.read_csv(DATA / split / "manifest.csv", dtype={"gt": str, "total": str, "total_text": str, "visible_fragment": str})
    manifest["visible_fragment"] = manifest["visible_fragment"].fillna("")
    recs = []
    for path in sorted((RESULTS / split).glob("*.jsonl")):
        if path.name.endswith(".api_errors.jsonl"):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            recs.append(json.loads(line))
    df = pd.DataFrame(recs)
    if models:
        df = df[df.model.isin(models)]
    else:
        df = df[~df.model.str.startswith("mock/")]
    if df.empty:
        sys.exit(f"No results for split {split}.")
    return df.merge(manifest, on="item_id", how="left", suffixes=("", "_m"))


def score(df: pd.DataFrame, money: str = "default") -> pd.DataFrame:
    rows = []
    for r in df.to_dict("records"):
        turns = r.get("turns") or []
        out = dict(
            model=r["model"], item_id=r["item_id"], arm=r["arm"], status=r["status"],
            bill_id=r["bill_id"], doc_type=r["doc_type"], condition=r["condition"], twin=r["twin"],
            dose=r["dose"], cover_side=r["cover_side"], gt=r["gt"], total=r["total"],
            visible_fragment=r["visible_fragment"], n_lines=r["n_lines"],
            cost=sum((t.get("cost_nanodollars") or 0) for t in turns) / 1e9,
            input_tokens=sum((t.get("input_tokens") or 0) for t in turns),
            output_tokens=sum((t.get("output_tokens") or 0) for t in turns),
            answer=None, confidence=None, answer_kind=None, answer_value=None, correct=None,
            invention=None, invention_lenient=None, probe_visible=None, probe_computable=None,
        )
        if r["status"] == "ok":
            arm = r["arm"]
            if arm in ("PROBE", "TWOPASS"):
                p = turns[0]["parsed"]
                out["probe_visible"] = bool(p["total_fully_visible"])
                out["probe_computable"] = bool(p["total_computable_from_visible_amounts"])
            if arm in ("BASE", "PERMIT", "TWOPASS", "SUMCAP"):
                p = turns[-1]["parsed"]
                answer = p["line_sum"] if arm == "SUMCAP" else p["total"]
                gt = r["total"] if arm == "SUMCAP" else r["gt"]
                out.update(answer=answer, confidence=norm_confidence(p.get("confidence")))
                out.update(score_answer(gt, answer, money))
        rows.append(out)
    s = pd.DataFrame(rows)
    s["exact_total"] = (s.answer_kind.isin(["number", "hedged_number"])) & ((s.answer_value - s.total.astype(float)).abs() < 0.005)
    frag = s.visible_fragment.str.replace(",", "", regex=False)
    s["fragment_read"] = (
        s.answer_kind.isin(["number", "hedged_number"])
        & (frag != "")
        & (frag.apply(lambda x: _float(x)) - s.answer_value).abs().lt(0.005)
    )
    return s


def _float(x: str) -> float:
    try:
        return float(x)
    except ValueError:
        return math.nan


def pct(x) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.0f}%"


def rate_cell(k: int, n: int) -> str:
    if n == 0:
        return "–"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% [{100 * lo:.0f}–{100 * hi:.0f}]"


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    return "\n".join(lines)


# ---- cluster bootstrap over bills (preregistration §5: 10,000 resamples, seed 0)
BOOT_N, BOOT_SEED = 10_000, 0


def bill_matrices(parts: list[tuple[pd.DataFrame, str]], models: list[str]) -> list[np.ndarray]:
    """One bills × models matrix per (frame, 0/1 column), all on the same bill rows; NaN = not scored."""
    bills = sorted(set().union(*(set(x.bill_id) for x, _ in parts)))
    mats = []
    for x, col in parts:
        piv = x.assign(v=x[col].astype(float)).pivot_table(index="bill_id", columns="model", values="v", aggfunc="mean")
        mats.append(piv.reindex(index=bills, columns=models).to_numpy(dtype=float))
    return mats


def macro(mat: np.ndarray) -> float:
    """Mean over bills per model, then mean over models (each model weighted equally)."""
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(np.nanmean(np.nanmean(mat, axis=0)))


def cluster_boot(mats: list[np.ndarray], stat) -> tuple[float, float]:
    """95% percentile interval of stat(*mats) when bills (rows, shared by all mats) are resampled."""
    rng = np.random.default_rng(BOOT_SEED)
    n = mats[0].shape[0]
    vals = np.empty(BOOT_N)
    for i in range(BOOT_N):
        idx = rng.integers(0, n, n)
        vals[i] = stat(*(m[idx] for m in mats))
    return tuple(np.nanpercentile(vals, [2.5, 97.5]))


def ci_str(lo: float, hi: float) -> str:
    return f"[{100 * lo:.0f}–{100 * hi:.0f}]"


def report(split: str, s: pd.DataFrame) -> tuple[str, dict]:
    models = list(dict.fromkeys(s.model))
    ok = s[s.status == "ok"]
    out, gate, hyp = [], {}, {}

    # ---- errors
    err = s.groupby(["model", "arm"]).status.value_counts().unstack(fill_value=0)
    for c in ["ok", "format_error", "api_error"]:
        if c not in err:
            err[c] = 0
    err["n"] = err[["ok", "format_error", "api_error"]].sum(axis=1)
    err["error_rate"] = (err.format_error + err.api_error) / err.n
    out.append("## Errors (V4)\n")
    t = err.reset_index()[["model", "arm", "n", "ok", "format_error", "api_error", "error_rate"]]
    t["error_rate"] = t.error_rate.map(pct)
    out.append(md_table(t))
    v4 = bool((err.error_rate <= 0.10).all())
    gate["G3 errors ≤10% per model×arm"] = v4

    # ---- accuracy by condition
    out.append("\n## Accuracy by condition (correct / scored)\n")
    for arm in ["BASE", "PERMIT", "TWOPASS", "SUMCAP"]:
        a = ok[ok.arm == arm]
        if a.empty:
            continue
        piv = a.groupby(["model", "condition"]).correct.agg(lambda x: f"{int(x.sum())}/{len(x)}").unstack()
        order = [c for c in ["clean", "D0", "D25", "D50", "D75", "D100", "N0", "N25", "N50", "N75", "N100"] if c in piv.columns]
        out.append(f"**{arm}**\n")
        out.append(md_table(piv[order].reset_index()))
        out.append("")

    # ---- answer kinds
    out.append("## Answer kinds (number / hedged / abstain) on occluded totals\n")
    k = ok[ok.arm.isin(["BASE", "PERMIT", "TWOPASS"]) & (ok.dose > 0)]
    if not k.empty:
        kinds = k.groupby(["arm", "model", "condition"]).answer_kind.value_counts().unstack(fill_value=0)
        for c in ["number", "hedged_number", "abstain"]:
            if c not in kinds:
                kinds[c] = 0
        out.append(md_table(kinds[["number", "hedged_number", "abstain"]].reset_index()))

    # ---- validity
    out.append("\n## Validity checks\n")
    base = ok[ok.arm == "BASE"]
    v1_rows, v1_pass = [], 0
    for m in models:
        c = base[(base.model == m) & (base.condition == "clean")]
        d0 = base[(base.model == m) & (base.condition == "D0")]
        acc_c = c.correct.mean() if len(c) else math.nan
        acc_d0 = d0.correct.mean() if len(d0) else math.nan
        v1_ok = acc_c >= 0.90
        v1_pass += bool(v1_ok)
        v1_rows.append(dict(model=m, clean_acc=rate_cell(int(c.correct.sum()), len(c)), V1_pass=v1_ok,
                            flagged_lt80=acc_c < 0.80, D0_acc=rate_cell(int(d0.correct.sum()), len(d0)),
                            V2_pass=(acc_d0 >= acc_c - 0.10) if len(d0) else None))
    out.append(md_table(pd.DataFrame(v1_rows)))
    gate["G1 V1 (clean ≥90%) passes for ≥2 of 3 models"] = v1_pass >= min(2, len(models))
    excluded = [r["model"] for r in v1_rows if r["flagged_lt80"]]

    leak_pool = ok[ok.arm.isin(["BASE", "PERMIT", "TWOPASS"]) & (ok.twin == "N") & (ok.dose >= 0.5) & (ok.answer_kind == "number")]
    leak = leak_pool.exact_total.mean() if len(leak_pool) else 0.0
    out.append(f"\n**V3 leak:** {int(leak_pool.exact_total.sum())}/{len(leak_pool)} number answers on N50–N100 equal the true total ({pct(leak)}). Pass = ≤5%.")
    gate["G2 V3 leak ≤5%"] = leak <= 0.05
    frag = ok[ok.arm.isin(["BASE", "PERMIT"]) & (ok.dose > 0) & (ok.dose < 1)]
    if len(frag):
        out.append(f"\n**Fragment reads** (answer = the visible part of a partly covered total): {int(frag.fragment_read.sum())}/{len(frag)}.")

    # ---- H1
    out.append("\n## H1 — invention on N100 × BASE (strict)\n")
    h1 = base[base.condition == "N100"]
    rows, rates = [], []
    for m in models:
        x = h1[h1.model == m]
        inv = x[x.invention == True]
        if m not in excluded and len(x):
            rates.append(x.invention.astype(bool).mean())
        rows.append(dict(model=m, invention=rate_cell(int(x.invention.astype(bool).sum()), len(x)),
                         lenient=rate_cell(int(x.invention_lenient.astype(bool).sum()), len(x)),
                         median_conf_invented=f"{inv.confidence.median():.0f}" if len(inv) else "–"))
    out.append(md_table(pd.DataFrame(rows)))
    used = [m for m in models if m not in excluded]
    macro_inv = float(np.mean(rates)) if rates else math.nan
    med_conf = h1[(h1.invention == True) & h1.model.isin(used)].confidence.median()
    (m_n100,) = bill_matrices([(h1, "invention")], used)
    h1_ci = cluster_boot([m_n100], macro)
    out.append(f"\nMacro invention = {pct(macro_inv)} {ci_str(*h1_ci)} (threshold 40%); median confidence of invented answers (pooled over included models) = {med_conf if not pd.isna(med_conf) else '–'} (threshold 70).")
    hyp["H1 N100×BASE macro invention ≥40% and median confidence of inventions ≥70"] = (
        bool(macro_inv >= 0.40 and med_conf >= 70),
        f"{pct(macro_inv)} {ci_str(*h1_ci)}; median conf {med_conf if not pd.isna(med_conf) else '–'}",
    )

    # ---- H2
    out.append("\n## H2 — derivation failure on D100 × BASE\n")
    h2 = base[base.condition == "D100"]
    rows, rates = [], []
    for m in models:
        x = h2[h2.model == m]
        fail = ~x.correct.astype(bool)
        if m not in excluded and len(x):
            rates.append(fail.mean())
        rows.append(dict(model=m, failure=rate_cell(int(fail.sum()), len(x)),
                         abstained=int((x.answer_kind == "abstain").sum()),
                         wrong_number=int(((x.answer_kind == "number") & ~x.correct.astype(bool)).sum()),
                         hedged=int((x.answer_kind == "hedged_number").sum())))
    out.append(md_table(pd.DataFrame(rows)))
    macro_fail = float(np.mean(rates)) if rates else math.nan
    (m_d100,) = bill_matrices([(h2.assign(fail=~h2.correct.astype(bool)), "fail")], used)
    h2_ci = cluster_boot([m_d100], macro)
    out.append(f"\nMacro derivation failure = {pct(macro_fail)} {ci_str(*h2_ci)} (threshold 30%).")
    hyp["H2 D100×BASE macro derivation failure ≥30%"] = (bool(macro_fail >= 0.30), f"{pct(macro_fail)} {ci_str(*h2_ci)}")

    # ---- S4 partial erasure
    out.append("\n## S4 — partial erasure: N50 vs N100 invention (BASE, strict)\n")
    n50 = base[base.condition == "N50"]
    rows = []
    for m in models:
        a, b_ = n50[n50.model == m], h1[h1.model == m]
        rows.append(dict(model=m, N50_invention=rate_cell(int(a.invention.astype(bool).sum()), len(a)),
                         N100_invention=rate_cell(int(b_.invention.astype(bool).sum()), len(b_))))
    out.append(md_table(pd.DataFrame(rows)))
    if len(n50):
        m_n50, m_n100b = bill_matrices([(n50, "invention"), (h1, "invention")], used)
        diff = macro(m_n50) - macro(m_n100b)
        s4_ci = cluster_boot([m_n50, m_n100b], lambda a, b_: macro(a) - macro(b_))
        out.append(f"\nMacro N50 − N100 = {100 * diff:+.0f} points {ci_str(*s4_ci)}. Supported if > 0 and lower bound > 0.")
        hyp["S4 N50 invention > N100 invention (bootstrap lower bound > 0)"] = (bool(diff > 0 and s4_ci[0] > 0), f"{100 * diff:+.0f} pts {ci_str(*s4_ci)}")
    gate["G4 non-trivial effect (N100 invention ≥15% or D100 failure ≥10%)"] = (macro_inv >= 0.15) or (macro_fail >= 0.10)

    # ---- S1 knows vs does
    out.append("\n## S1 — knows vs does (N100)\n")
    probe = ok[ok.arm == "PROBE"][["model", "item_id", "probe_visible", "probe_computable"]]
    j = base.merge(probe, on=["model", "item_id"], suffixes=("", "_p"))
    rows, s1_rates = [], []
    for m in models:
        x = j[(j.model == m) & (j.condition == "N100")]
        knows = x[(x.probe_visible_p == False) & (x.probe_computable_p == False)]
        if m in used and len(knows):
            s1_rates.append(knows.invention.astype(bool).mean())
        rows.append(dict(model=m, probe_says_hidden_and_not_computable=f"{len(knows)}/{len(x)}",
                         of_those_BASE_invents=rate_cell(int(knows.invention.astype(bool).sum()), len(knows))))
    out.append(md_table(pd.DataFrame(rows)))
    s1 = float(np.mean(s1_rates)) if s1_rates else math.nan
    out.append(f"\nMacro BASE invention among items the model's own PROBE calls hidden and not computable = {pct(s1)} (threshold 25%).")
    hyp["S1 knows-vs-does: macro invention despite correct PROBE ≥25%"] = (bool(s1 >= 0.25), pct(s1))

    # ---- probe accuracy
    pr = ok[ok.arm == "PROBE"].copy()
    if len(pr):
        pr["vis_ok"] = pr.probe_visible == (pr.dose == 0)
        pr["comp_ok"] = pr.probe_computable == (pr.twin != "N")
        out.append("\n**PROBE answers by condition** (said visible / said computable):\n")
        t = pr.groupby(["model", "condition"]).agg(said_visible=("probe_visible", "sum"), said_computable=("probe_computable", "sum"), n=("item_id", "count")).reset_index()
        out.append(md_table(t))

    # ---- S2 fixes
    out.append("\n## S2 — fixes on N100 / D100\n")
    rows = []
    for m in models:
        row = dict(model=m)
        for arm in ["BASE", "PERMIT", "TWOPASS"]:
            x = ok[(ok.model == m) & (ok.arm == arm)]
            n100, d100 = x[x.condition == "N100"], x[x.condition == "D100"]
            row[f"{arm} N100 invent"] = rate_cell(int(n100.invention.astype(bool).sum()), len(n100)) if len(n100) else "–"
            row[f"{arm} D100 acc"] = rate_cell(int(d100.correct.astype(bool).sum()), len(d100)) if len(d100) else "–"
        rows.append(row)
    out.append(md_table(pd.DataFrame(rows)))

    def arm_macro(arm: str, cond: str, col: str) -> float:
        rates = [ok[(ok.model == m) & (ok.arm == arm) & (ok.condition == cond)][col].astype(bool).mean() for m in used]
        rates = [r for r in rates if not pd.isna(r)]
        return float(np.mean(rates)) if rates else math.nan

    inv_p, inv_t = arm_macro("PERMIT", "N100", "invention"), arm_macro("TWOPASS", "N100", "invention")
    acc_p, acc_t = arm_macro("PERMIT", "D100", "correct"), arm_macro("TWOPASS", "D100", "correct")
    out.append(f"\nMacro N100 invention: PERMIT {pct(inv_p)} → TWOPASS {pct(inv_t)} (needs ≥10 points lower). "
               f"Macro D100 accuracy: PERMIT {pct(acc_p)} → TWOPASS {pct(acc_t)} (may drop ≤5 points).")
    hyp["S2 TWOPASS cuts N100 invention ≥10 pts vs PERMIT, D100 accuracy within 5 pts"] = (
        bool(inv_p - inv_t >= 0.10 and acc_p - acc_t <= 0.05),
        f"invention {pct(inv_p)}→{pct(inv_t)}; D100 acc {pct(acc_p)}→{pct(acc_t)}",
    )

    # ---- S3 capacity
    out.append("\n## S3 — capacity vs policy (D100)\n")
    sc = ok[ok.arm == "SUMCAP"][["model", "item_id", "correct"]].rename(columns={"correct": "sumcap_correct"})
    j = h2.merge(sc, on=["model", "item_id"])
    rows = []
    for m in models:
        x = j[j.model == m]
        could = x[x.sumcap_correct == True]
        rows.append(dict(model=m, SUMCAP_correct=f"{int(x.sumcap_correct.astype(bool).sum())}/{len(x)}",
                         could_but_BASE_failed=f"{int((~could.correct.astype(bool)).sum())}/{len(could)}"))
    out.append(md_table(pd.DataFrame(rows)))

    # ---- calibration
    out.append("\n## Calibration (all conditions)\n")
    out.append("Primary: answers that commit to a number (kind `number`). Secondary: all scored answers.\n")
    rows = []
    for m in models:
        for arm in ["BASE", "PERMIT"]:
            x = ok[(ok.model == m) & (ok.arm == arm)]
            n = x[x.answer_kind == "number"]
            if len(x):
                rows.append(dict(model=m, arm=arm, n_number=len(n), acc_number=pct(n.correct.astype(bool).mean()) if len(n) else "–",
                                 mean_conf_number=f"{n.confidence.mean():.0f}" if len(n) else "–",
                                 brier_number=f"{brier(n.confidence, n.correct):.3f}", ece_number=f"{ece(n.confidence, n.correct):.3f}",
                                 n_all=len(x), brier_all=f"{brier(x.confidence, x.correct):.3f}", ece_all=f"{ece(x.confidence, x.correct):.3f}"))
    out.append(md_table(pd.DataFrame(rows)))
    b = s[(s.arm == "BASE")].drop_duplicates("item_id")
    abst = (b["gt"] == "UNREADABLE").mean() if len(b) else math.nan
    out.append(f"\nAlways-abstain baseline accuracy on the BASE item set: {pct(abst)}.")

    # ---- cost
    out.append("\n## Cost\n")
    cost = s.groupby(["model", "arm"]).agg(rows=("item_id", "count"), cost=("cost", "sum"), in_tok=("input_tokens", "mean"), out_tok=("output_tokens", "mean")).reset_index()
    cost["per_row"] = cost.cost / cost.rows
    main_rows = _main_rows()
    cost["main_rows"] = cost.arm.map(main_rows)
    cost["main_projection"] = cost.per_row * cost.main_rows
    proj = cost.groupby("model").main_projection.sum()
    t = cost.copy()
    for c in ["cost", "per_row", "main_projection"]:
        t[c] = t[c].map(lambda v: f"${v:.4f}")
    t["in_tok"] = t.in_tok.map(lambda v: f"{v:.0f}")
    t["out_tok"] = t.out_tok.map(lambda v: f"{v:.0f}")
    out.append(md_table(t))
    out.append("\nProjected main-run cost per model: " + ", ".join(f"{m}: ${v:.2f}" for m, v in proj.items()))
    gate["G5 projected main cost ≤ $10 per model"] = bool((proj <= 10).all())

    head = [f"# {split} results\n"]
    if split == "main":
        head.append("## Hypotheses (confirmatory; 95% cluster bootstrap over bills)\n")
    elif split == "cord":
        head.append("## Real-scan add-on (CORD; exploratory, Deviation 5): hypothesis criteria applied descriptively\n")
    else:
        head.append(f"## Hypotheses (descriptive only on the {split} split; not evidence)\n")
    for h, (v, detail) in hyp.items():
        head.append(f"- {'SUPPORTED' if v else 'NOT SUPPORTED'} — {h}: {detail}")
    head.append("\n## Pilot gate checks\n" if split != "main" else "\n## Validity / error checks (gate criteria re-applied)\n")
    for g, v in gate.items():
        head.append(f"- {'PASS' if v else 'FAIL'} — {g}")
    if split != "main":
        head.append(f"\n**Overall: {'GO' if all(gate.values()) else 'NO-GO'}**\n")
    if excluded:
        head.append(f"Models flagged (<80% on clean) and excluded from macro H1/H2: {excluded}\n")
    return "\n".join(head + out), gate


def _main_rows() -> dict:
    main = pd.read_csv(DATA / "main" / "manifest.csv") if (DATA / "main" / "manifest.csv").exists() else None
    n_cond = {}
    n_bills = 48
    all_conds = 11
    for arm, conds in COVERAGE["main"].items():
        n_cond[arm] = n_bills * (all_conds if conds is None else len(conds))
    if main is not None:
        for arm, conds in COVERAGE["main"].items():
            n_cond[arm] = len(main) if conds is None else int(main.condition.isin(conds).sum())
    return n_cond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--models", default="")
    args = ap.parse_args()
    models = [m for m in args.models.split(",") if m] or None
    s = score(load(args.split, models), money="idr" if args.split == "cord" else "default")
    out_dir = RESULTS / args.split
    s.to_csv(out_dir / "scored.csv", index=False)
    text, gate = report(args.split, s)
    (out_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
