# Pilot report — Erased Totals (2026-10-11)

Pilot = 12 bills × 6 conditions = 72 images; 3 models (Anthropic, Google, OpenAI); 252 calls per
model. Full tables: `results/pilot/report.md`; per-response scores: `results/pilot/scored.csv`.
Pilot numbers are **not** confirmatory (n = 12 bills per cell). Spend ≈ $2.16.

## Gate: GO (all five checks pass)

| Check | Result |
|---|---|
| G1 legibility (clean ≥ 90%) | 3/3 models at 12/12; placebo D0 also 12/12 for all |
| G2 leak | 0/76 invented numbers equal the true total |
| G3 errors ≤ 10% | 0 after Deviation 3 (3 Sonnet calls were cut off at 2048 tokens; re-run at 8192) |
| G4 non-trivial effect | N100 invention 47% macro |
| G5 cost | main projection: Sonnet $8.36, Gemini $6.45, nano $0.42 (each fits a day, not together) |

## What the pilot shows

| | Sonnet 5 | Gemini 3 Flash | GPT-5.4 nano |
|---|---|---|---|
| N100 × BASE: gives a number (strict) | 6/12 | 3/12 | 8/12 |
| … median confidence of those numbers | **20** | **95** | 62 |
| N50 × BASE: gives a number | 12/12 | 12/12 | 12/12 |
| D100 × BASE: derives the erased total | 12/12 | 12/12 | 2/12 |
| SUMCAP (told to add the lines) | 12/12 | 12/12 | 2/12 |
| PROBE on N100: "not visible, not computable" | 12/12 | 12/12 | 12/12 |
| PERMIT N100 invention | 1/12 | 0/12 | 3/12 |
| PERMIT D100 accuracy | 11/12 | 9/12 | 2/12 |
| TWOPASS N100 invention | 0/12 | 0/12 | 0/12 |
| TWOPASS D100 accuracy | 12/12 | 12/12 | 0/12 |

1. **H1 is half-supported.** Invention happens (macro 47% ≥ 40%), but the "confidently" clause
   fails (pooled median 55 < 70) because Sonnet attaches low confidence (5–45) to its guesses.
   Gemini invents less often but at 95–100.
2. **H2 is not supported as a policy failure.** Strong models derive the erased total every time;
   nano's failures are capacity (it can't add these bills even when told to: SUMCAP 2/12, errors
   of ±50–500). The prereg fallback ("lead with the derivable twin") looks weak.
3. **Partial erasure is the strongest effect.** With half the total covered and one line hidden
   (N50), every model gives a number on 12/12 bills. Sonnet and Gemini keep the visible digits and
   invent the covered ones to match (`███.35` → 231.35 at 95% confidence); nano reads out the visible
   fragment (`0.35`, `3.65`).
4. **Knows vs does.** All three models correctly say in a separate probe that the N100 total is
   neither visible nor computable (12/12), yet still invent it under BASE (25–67%).
5. **Fixes.** "You may say UNREADABLE" cuts invention but makes Gemini give up on derivable totals
   (D100 12/12 → 9/12). Two-pass (check, then extract) removes invention for all three and keeps
   derivation for Sonnet and Gemini, but makes nano abstain on every derivable item.
6. **Calibration.** On committed numbers under BASE: Gemini states 98 on average at 76% accuracy;
   nano 86 at 41%; Sonnet 79 at 75%.

## Decisions needed before the main run (log any change as a Deviation first)

- Proceed with H1/H2 unchanged (they are preregistered; the pilot is not evidence).
- Optional pre-main secondary hypothesis informed by the pilot (tested on fresh main bills):
  invention on N50 ≥ invention on N100 under BASE ("partial erasure is worse").
- Optional exploratory metric: share of inventions stated at confidence ≥ 70.
- Main models: pilot three + `google/gemini-3.1-flash-lite-preview` (vision check first).
- Budget: run one model per day (Sonnet ~$8.4, Gemini ~$6.5), nano + Flash-Lite together.

## Decisions taken (2026-10-11; preregistration Deviation 4)

- H1/H2 unchanged. S4 added (N50 invention > N100 invention under BASE, tested on main bills only).
- Flash-Lite passed the vision check (read 132.70 on the smoke bill) and joins the main run.
- Schedule: day 1 nano + Flash-Lite, day 2 Gemini 3 Flash, day 3 Sonnet 5, each with a spend cap.
- Main split rendered (528 images, manifest SHA-256 `53d10bdb…`); oracle dry run 100%.
