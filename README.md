# Erased Totals

Do vision models read a total that isn't there? We tape over the total on a bill (and, in the
"can't tell" condition, one line item too) and check whether models say they can't tell, make a
number up, or work the total out from the line items.

Kaggle benchmark (96-image task, `kaggle_task.py`): https://www.kaggle.com/benchmarks/tasks/ainazu/erased-totals

Video walkthrough (2 min): https://youtu.be/LA2v5tQWcqg

Write-up: `docs/post_dev.md`. Preregistration and dated deviation log: `docs/preregistration.md`.
Pilot report: `docs/pilot_report.md`.

## Layout

| Path | What |
|---|---|
| `bench/render.py` | Seeded renderer for the synthetic bills; exact ground truth; `python -m bench.render --split pilot\|main` |
| `bench/cord.py` | Real-receipt add-on built from CORD v2 (pinned revision + SHA-256) |
| `bench/prompts.py` | Exact prompt texts, response schemas, arm × condition coverage |
| `bench/runner.py` | Runs one model over a split with `kaggle-benchmarks`, per-call disk cache, spend cap |
| `bench/scoring.py` | Deterministic scoring (regex, no LLM judge) |
| `bench/analyze.py` | Hypotheses, validity checks, cluster bootstrap; writes `results/<split>/report.md` |
| `bench/figures.py` | Charts in `docs/figures/` |
| `data/<split>/` | Images, `manifest.csv` (ground truth), `MANIFEST.json` (hashes) |
| `results/<split>/` | Raw model responses (`*.jsonl`), `scored.csv`, `report.md` |

## Reproduce

Python 3.12+, `kaggle-benchmarks` 0.6.1, `pandas`, `pillow`, `pyarrow`, `matplotlib`, `python-dotenv`.
Model calls need your own Kaggle Benchmarks model-proxy credentials in `.env` (`kaggle b init`).

```
python -m bench.render --split main
python -m bench.runner --split main --model google/gemini-3-flash-preview --max-spend 9
python -m bench.analyze --split main
python -m bench.figures
```

The CORD add-on needs the two pinned CORD v2 parquet files in `data/cord_raw/` (see
`bench/cord.py` for URLs and hashes), then `python -m bench.cord`.

## Data credits

Real-receipt images in `data/cord/` are derived (amounts taped) from CORD v2,
`naver-clova-ix/cord-v2` on Hugging Face, licensed CC-BY-4.0: Park et al., "CORD: A Consolidated
Receipt Dataset for Post-OCR Parsing" (2019). All other bills are synthetic, with fictional
issuers.
