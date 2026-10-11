"""Charts for the write-up, from results/<split>/scored.csv (run bench.analyze first).

    python -m bench.figures
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "figures"

SHORT = {
    "anthropic/claude-sonnet-5@default": "Claude Sonnet 5",
    "google/gemini-3-flash-preview": "Gemini 3 Flash",
    "google/gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash-Lite",
    "openai/gpt-5.4-nano-2026-03-17": "GPT-5.4 nano",
}
ORDER = list(SHORT)
KIND_COLORS = {"number": "#d1495b", "hedged_number": "#edae49", "abstain": "#00798c"}


def load(split: str) -> pd.DataFrame:
    s = pd.read_csv(REPO / "results" / split / "scored.csv", dtype={"gt": str, "total": str})
    s = s[(s.status == "ok") & s.model.isin(ORDER)]
    for c in ("correct", "invention", "probe_visible", "probe_computable"):
        s[c] = s[c].map({True: True, False: False, "True": True, "False": False})
    return s


def pct(x) -> float:
    return 100 * float(x.mean()) if len(x) else float("nan")


def style(ax, title: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of bills")


def fig_invention(s: pd.DataFrame) -> None:
    """What each model answers when the total is hidden and cannot be worked out."""
    b = s[s.arm == "BASE"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, cond, title in ((axes[0], "N100", "Total fully taped"), (axes[1], "N50", "Total half taped")):
        x = b[b.condition == cond]
        models = [m for m in ORDER if m in set(x.model)]
        bottom = [0.0] * len(models)
        for kind, label in (("number", "gives a number"), ("hedged_number", "number + caveat"), ("abstain", "says unreadable")):
            vals = [pct(x[x.model == m].answer_kind == kind) for m in models]
            ax.bar([SHORT[m] for m in models], vals, bottom=bottom, color=KIND_COLORS[kind], label=label)
            bottom = [a + v for a, v in zip(bottom, vals)]
        style(ax, f"{title}; one line item also taped")
        ax.tick_params(axis="x", labelrotation=15)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="lower center", ncol=3, fontsize=10)
    fig.suptitle("The right answer is \"can't tell\". Red = the model made up a total.", x=0.01, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT / "invention.png", dpi=160)
    plt.close(fig)


def fig_knows_vs_does(s: pd.DataFrame) -> None:
    probe = s[(s.arm == "PROBE") & (s.condition == "N100")]
    base = s[(s.arm == "BASE") & (s.condition == "N100")]
    models = [m for m in ORDER if m in set(probe.model)]
    knows = [pct((probe[probe.model == m].probe_visible == False) & (probe[probe.model == m].probe_computable == False)) for m in models]
    does = [pct(base[base.model == m].answer_kind == "number") for m in models]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    xs = range(len(models))
    ax.bar([i - 0.2 for i in xs], knows, width=0.4, color="#00798c", label="asked: \"is it hidden and not computable?\" says yes")
    ax.bar([i + 0.2 for i in xs], does, width=0.4, color="#d1495b", label="asked for the total: makes one up")
    ax.set_xticks(list(xs), [SHORT[m] for m in models], rotation=10)
    style(ax, "They know the total is gone, and answer anyway")
    fig.legend(frameon=False, fontsize=9, loc="lower center", ncol=2)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT / "knows_vs_does.png", dpi=160)
    plt.close(fig)


def fig_fix(s: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    arms = [("BASE", "plain question", "#8d99ae"), ("PERMIT", "\"you may say UNREADABLE\"", "#edae49"), ("TWOPASS", "check first, then answer", "#00798c")]
    for ax, cond, col, title in ((axes[0], "N100", "invention", "Made-up totals (lower is better)"),
                                 (axes[1], "D100", "correct", "Worked out a recoverable total (higher is better)")):
        x = s[s.condition == cond]
        models = [m for m in ORDER if m in set(x.model)]
        w = 0.8 / len(arms)
        for k, (arm, label, color) in enumerate(arms):
            vals = []
            for m in models:
                y = x[(x.model == m) & (x.arm == arm)]
                vals.append(pct(y.answer_kind == "number") if col == "invention" else pct(y.correct == True))
            ax.bar([i - 0.4 + w * (k + 0.5) for i in range(len(models))], vals, width=w, color=color, label=label)
        ax.set_xticks(range(len(models)), [SHORT[m] for m in models], rotation=15)
        style(ax, title)
    axes[0].legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "fix.png", dpi=160)
    plt.close(fig)


def fig_confidence(s: pd.DataFrame) -> None:
    x = s[(s.arm == "BASE") & s.condition.isin(["N50", "N100"]) & (s.answer_kind == "number")]
    models = [m for m in ORDER if m in set(x.model)]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    data = [x[x.model == m].confidence.dropna() for m in models]
    ax.boxplot(data, tick_labels=[SHORT[m] for m in models], showfliers=True)
    ax.set_ylim(0, 105)
    ax.set_ylabel("stated confidence (0–100)")
    ax.set_title("How sure they say they are about made-up totals (half or fully taped)", loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelrotation=10)
    fig.tight_layout()
    fig.savefig(OUT / "confidence.png", dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    s = load("main")
    fig_invention(s)
    fig_knows_vs_does(s)
    fig_fix(s)
    fig_confidence(s)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
