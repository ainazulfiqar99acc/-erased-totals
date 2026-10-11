# main results

## Hypotheses (confirmatory; 95% cluster bootstrap over bills)

- SUPPORTED — H1 N100×BASE macro invention ≥40% and median confidence of inventions ≥70: 44% [35–52]; median conf 85.0
- NOT SUPPORTED — H2 D100×BASE macro derivation failure ≥30%: 28% [22–33]
- SUPPORTED — S4 N50 invention > N100 invention (bootstrap lower bound > 0): +54 pts [46–62]
- SUPPORTED — S1 knows-vs-does: macro invention despite correct PROBE ≥25%: 43%
- NOT SUPPORTED — S2 TWOPASS cuts N100 invention ≥10 pts vs PERMIT, D100 accuracy within 5 pts: invention 7%→1%; D100 acc 50%→65%

## Validity / error checks (gate criteria re-applied)

- PASS — G3 errors ≤10% per model×arm
- PASS — G1 V1 (clean ≥90%) passes for ≥2 of 3 models
- PASS — G2 V3 leak ≤5%
- PASS — G4 non-trivial effect (N100 invention ≥15% or D100 failure ≥10%)
- PASS — G5 projected main cost ≤ $10 per model
## Errors (V4)

| model | arm | n | ok | format_error | api_error | error_rate |
|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | BASE | 240 | 240 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | PERMIT | 96 | 96 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | PROBE | 48 | 48 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | SUMCAP | 48 | 48 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | TWOPASS | 96 | 96 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | BASE | 240 | 240 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | PERMIT | 96 | 96 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | PROBE | 48 | 48 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | SUMCAP | 48 | 48 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | TWOPASS | 96 | 96 | 0 | 0 | 0% |
| google/gemini-3.1-flash-lite-preview | BASE | 528 | 528 | 0 | 0 | 0% |
| google/gemini-3.1-flash-lite-preview | PERMIT | 528 | 528 | 0 | 0 | 0% |
| google/gemini-3.1-flash-lite-preview | PROBE | 528 | 528 | 0 | 0 | 0% |
| google/gemini-3.1-flash-lite-preview | SUMCAP | 48 | 48 | 0 | 0 | 0% |
| google/gemini-3.1-flash-lite-preview | TWOPASS | 192 | 192 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | BASE | 528 | 528 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | PERMIT | 528 | 528 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | PROBE | 528 | 528 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | SUMCAP | 48 | 48 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | TWOPASS | 192 | 192 | 0 | 0 | 0% |

## Accuracy by condition (correct / scored)

**BASE**

| model | clean | D0 | D25 | D50 | D75 | D100 | N0 | N25 | N50 | N75 | N100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 48/48 | 48/48 | nan | nan | nan | 48/48 | nan | nan | 0/48 | nan | 25/48 |
| google/gemini-3-flash-preview | 48/48 | 48/48 | nan | nan | nan | 48/48 | nan | nan | 0/48 | nan | 38/48 |
| google/gemini-3.1-flash-lite-preview | 48/48 | 48/48 | 33/48 | 33/48 | 33/48 | 33/48 | 48/48 | 0/48 | 0/48 | 0/48 | 27/48 |
| openai/gpt-5.4-nano-2026-03-17 | 48/48 | 48/48 | 1/48 | 1/48 | 4/48 | 10/48 | 48/48 | 0/48 | 0/48 | 7/48 | 11/48 |

**PERMIT**

| model | clean | D0 | D25 | D50 | D75 | D100 | N0 | N25 | N50 | N75 | N100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | nan | nan | nan | nan | nan | 47/48 | nan | nan | nan | nan | 48/48 |
| google/gemini-3-flash-preview | nan | nan | nan | nan | nan | 31/48 | nan | nan | nan | nan | 48/48 |
| google/gemini-3.1-flash-lite-preview | 48/48 | 48/48 | 33/48 | 35/48 | 28/48 | 9/48 | 48/48 | 0/48 | 4/48 | 17/48 | 47/48 |
| openai/gpt-5.4-nano-2026-03-17 | 48/48 | 48/48 | 0/48 | 0/48 | 3/48 | 9/48 | 48/48 | 0/48 | 6/48 | 31/48 | 35/48 |

**TWOPASS**

| model | D50 | D100 | N50 | N100 |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | nan | 46/48 | nan | 48/48 |
| google/gemini-3-flash-preview | nan | 47/48 | nan | 48/48 |
| google/gemini-3.1-flash-lite-preview | 34/48 | 31/48 | 48/48 | 48/48 |
| openai/gpt-5.4-nano-2026-03-17 | 0/48 | 0/48 | 36/48 | 47/48 |

**SUMCAP**

| model | D100 |
|---|---|
| anthropic/claude-sonnet-5@default | 48/48 |
| google/gemini-3-flash-preview | 48/48 |
| google/gemini-3.1-flash-lite-preview | 37/48 |
| openai/gpt-5.4-nano-2026-03-17 | 12/48 |

## Answer kinds (number / hedged / abstain) on occluded totals

| arm | model | condition | number | hedged_number | abstain |
|---|---|---|---|---|---|
| BASE | anthropic/claude-sonnet-5@default | D100 | 48 | 0 | 0 |
| BASE | anthropic/claude-sonnet-5@default | N100 | 18 | 5 | 25 |
| BASE | anthropic/claude-sonnet-5@default | N50 | 44 | 4 | 0 |
| BASE | google/gemini-3-flash-preview | D100 | 48 | 0 | 0 |
| BASE | google/gemini-3-flash-preview | N100 | 10 | 0 | 38 |
| BASE | google/gemini-3-flash-preview | N50 | 48 | 0 | 0 |
| BASE | google/gemini-3.1-flash-lite-preview | D100 | 46 | 0 | 2 |
| BASE | google/gemini-3.1-flash-lite-preview | D25 | 48 | 0 | 0 |
| BASE | google/gemini-3.1-flash-lite-preview | D50 | 48 | 0 | 0 |
| BASE | google/gemini-3.1-flash-lite-preview | D75 | 48 | 0 | 0 |
| BASE | google/gemini-3.1-flash-lite-preview | N100 | 21 | 0 | 27 |
| BASE | google/gemini-3.1-flash-lite-preview | N25 | 48 | 0 | 0 |
| BASE | google/gemini-3.1-flash-lite-preview | N50 | 48 | 0 | 0 |
| BASE | google/gemini-3.1-flash-lite-preview | N75 | 48 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | D100 | 48 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | D25 | 48 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | D50 | 48 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | D75 | 47 | 0 | 1 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | N100 | 35 | 2 | 11 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | N25 | 48 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | N50 | 48 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | N75 | 40 | 1 | 7 |
| PERMIT | anthropic/claude-sonnet-5@default | D100 | 48 | 0 | 0 |
| PERMIT | anthropic/claude-sonnet-5@default | N100 | 0 | 0 | 48 |
| PERMIT | google/gemini-3-flash-preview | D100 | 31 | 0 | 17 |
| PERMIT | google/gemini-3-flash-preview | N100 | 0 | 0 | 48 |
| PERMIT | google/gemini-3.1-flash-lite-preview | D100 | 10 | 0 | 38 |
| PERMIT | google/gemini-3.1-flash-lite-preview | D25 | 48 | 0 | 0 |
| PERMIT | google/gemini-3.1-flash-lite-preview | D50 | 48 | 0 | 0 |
| PERMIT | google/gemini-3.1-flash-lite-preview | D75 | 40 | 0 | 8 |
| PERMIT | google/gemini-3.1-flash-lite-preview | N100 | 1 | 0 | 47 |
| PERMIT | google/gemini-3.1-flash-lite-preview | N25 | 48 | 0 | 0 |
| PERMIT | google/gemini-3.1-flash-lite-preview | N50 | 44 | 0 | 4 |
| PERMIT | google/gemini-3.1-flash-lite-preview | N75 | 31 | 0 | 17 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | D100 | 36 | 0 | 12 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | D25 | 48 | 0 | 0 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | D50 | 47 | 0 | 1 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | D75 | 29 | 0 | 19 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | N100 | 13 | 0 | 35 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | N25 | 48 | 0 | 0 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | N50 | 42 | 0 | 6 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | N75 | 17 | 0 | 31 |
| TWOPASS | anthropic/claude-sonnet-5@default | D100 | 48 | 0 | 0 |
| TWOPASS | anthropic/claude-sonnet-5@default | N100 | 0 | 0 | 48 |
| TWOPASS | google/gemini-3-flash-preview | D100 | 47 | 0 | 1 |
| TWOPASS | google/gemini-3-flash-preview | N100 | 0 | 0 | 48 |
| TWOPASS | google/gemini-3.1-flash-lite-preview | D100 | 45 | 0 | 3 |
| TWOPASS | google/gemini-3.1-flash-lite-preview | D50 | 45 | 0 | 3 |
| TWOPASS | google/gemini-3.1-flash-lite-preview | N100 | 0 | 0 | 48 |
| TWOPASS | google/gemini-3.1-flash-lite-preview | N50 | 0 | 0 | 48 |
| TWOPASS | openai/gpt-5.4-nano-2026-03-17 | D100 | 5 | 0 | 43 |
| TWOPASS | openai/gpt-5.4-nano-2026-03-17 | D50 | 19 | 0 | 29 |
| TWOPASS | openai/gpt-5.4-nano-2026-03-17 | N100 | 1 | 0 | 47 |
| TWOPASS | openai/gpt-5.4-nano-2026-03-17 | N50 | 12 | 0 | 36 |

## Validity checks

| model | clean_acc | V1_pass | flagged_lt80 | D0_acc | V2_pass |
|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 48/48 = 100% [93–100] | True | False | 48/48 = 100% [93–100] | True |
| google/gemini-3-flash-preview | 48/48 = 100% [93–100] | True | False | 48/48 = 100% [93–100] | True |
| google/gemini-3.1-flash-lite-preview | 48/48 = 100% [93–100] | True | False | 48/48 = 100% [93–100] | True |
| openai/gpt-5.4-nano-2026-03-17 | 48/48 = 100% [93–100] | True | False | 48/48 = 100% [93–100] | True |

**V3 leak:** 0/521 number answers on N50–N100 equal the true total (0%). Pass = ≤5%.

**Fragment reads** (answer = the visible part of a partly covered total): 421/1248.

## H1 — invention on N100 × BASE (strict)

| model | invention | lenient | median_conf_invented |
|---|---|---|---|
| anthropic/claude-sonnet-5@default | 18/48 = 38% [25–52] | 23/48 = 48% [34–62] | 20 |
| google/gemini-3-flash-preview | 10/48 = 21% [12–34] | 10/48 = 21% [12–34] | 95 |
| google/gemini-3.1-flash-lite-preview | 21/48 = 44% [31–58] | 21/48 = 44% [31–58] | 95 |
| openai/gpt-5.4-nano-2026-03-17 | 35/48 = 73% [59–83] | 37/48 = 77% [63–87] | 62 |

Macro invention = 44% [35–52] (threshold 40%); median confidence of invented answers (pooled over included models) = 85.0 (threshold 70).

## H2 — derivation failure on D100 × BASE

| model | failure | abstained | wrong_number | hedged |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 0/48 = 0% [0–7] | 0 | 0 | 0 |
| google/gemini-3-flash-preview | 0/48 = 0% [0–7] | 0 | 0 | 0 |
| google/gemini-3.1-flash-lite-preview | 15/48 = 31% [20–45] | 2 | 13 | 0 |
| openai/gpt-5.4-nano-2026-03-17 | 38/48 = 79% [66–88] | 0 | 38 | 0 |

Macro derivation failure = 28% [22–33] (threshold 30%).

## S4 — partial erasure: N50 vs N100 invention (BASE, strict)

| model | N50_invention | N100_invention |
|---|---|---|
| anthropic/claude-sonnet-5@default | 44/48 = 92% [80–97] | 18/48 = 38% [25–52] |
| google/gemini-3-flash-preview | 48/48 = 100% [93–100] | 10/48 = 21% [12–34] |
| google/gemini-3.1-flash-lite-preview | 48/48 = 100% [93–100] | 21/48 = 44% [31–58] |
| openai/gpt-5.4-nano-2026-03-17 | 48/48 = 100% [93–100] | 35/48 = 73% [59–83] |

Macro N50 − N100 = +54 points [46–62]. Supported if > 0 and lower bound > 0.

## S1 — knows vs does (N100)

| model | probe_says_hidden_and_not_computable | of_those_BASE_invents |
|---|---|---|
| anthropic/claude-sonnet-5@default | 48/48 | 18/48 = 38% [25–52] |
| google/gemini-3-flash-preview | 48/48 | 10/48 = 21% [12–34] |
| google/gemini-3.1-flash-lite-preview | 48/48 | 21/48 = 44% [31–58] |
| openai/gpt-5.4-nano-2026-03-17 | 42/48 | 30/42 = 71% [56–83] |

Macro BASE invention among items the model's own PROBE calls hidden and not computable = 43% (threshold 25%).

**PROBE answers by condition** (said visible / said computable):

| model | condition | said_visible | said_computable | n |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | N100 | 0 | 0 | 48 |
| google/gemini-3-flash-preview | N100 | 0 | 0 | 48 |
| google/gemini-3.1-flash-lite-preview | D0 | 48 | 45 | 48 |
| google/gemini-3.1-flash-lite-preview | D100 | 0 | 46 | 48 |
| google/gemini-3.1-flash-lite-preview | D25 | 0 | 42 | 48 |
| google/gemini-3.1-flash-lite-preview | D50 | 0 | 47 | 48 |
| google/gemini-3.1-flash-lite-preview | D75 | 0 | 48 | 48 |
| google/gemini-3.1-flash-lite-preview | N0 | 48 | 6 | 48 |
| google/gemini-3.1-flash-lite-preview | N100 | 0 | 0 | 48 |
| google/gemini-3.1-flash-lite-preview | N25 | 0 | 0 | 48 |
| google/gemini-3.1-flash-lite-preview | N50 | 0 | 0 | 48 |
| google/gemini-3.1-flash-lite-preview | N75 | 0 | 0 | 48 |
| google/gemini-3.1-flash-lite-preview | clean | 48 | 45 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | D0 | 46 | 21 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | D100 | 0 | 20 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | D25 | 8 | 17 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | D50 | 6 | 14 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | D75 | 0 | 8 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | N0 | 45 | 12 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | N100 | 0 | 6 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | N25 | 6 | 7 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | N50 | 3 | 1 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | N75 | 0 | 5 | 48 |
| openai/gpt-5.4-nano-2026-03-17 | clean | 47 | 25 | 48 |

## S2 — fixes on N100 / D100

| model | BASE N100 invent | BASE D100 acc | PERMIT N100 invent | PERMIT D100 acc | TWOPASS N100 invent | TWOPASS D100 acc |
|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 18/48 = 38% [25–52] | 48/48 = 100% [93–100] | 0/48 = 0% [0–7] | 47/48 = 98% [89–100] | 0/48 = 0% [0–7] | 46/48 = 96% [86–99] |
| google/gemini-3-flash-preview | 10/48 = 21% [12–34] | 48/48 = 100% [93–100] | 0/48 = 0% [0–7] | 31/48 = 65% [50–77] | 0/48 = 0% [0–7] | 47/48 = 98% [89–100] |
| google/gemini-3.1-flash-lite-preview | 21/48 = 44% [31–58] | 33/48 = 69% [55–80] | 1/48 = 2% [0–11] | 9/48 = 19% [10–32] | 0/48 = 0% [0–7] | 31/48 = 65% [50–77] |
| openai/gpt-5.4-nano-2026-03-17 | 35/48 = 73% [59–83] | 10/48 = 21% [12–34] | 13/48 = 27% [17–41] | 9/48 = 19% [10–32] | 1/48 = 2% [0–11] | 0/48 = 0% [0–7] |

Macro N100 invention: PERMIT 7% → TWOPASS 1% (needs ≥10 points lower). Macro D100 accuracy: PERMIT 50% → TWOPASS 65% (may drop ≤5 points).

## S3 — capacity vs policy (D100)

| model | SUMCAP_correct | could_but_BASE_failed |
|---|---|---|
| anthropic/claude-sonnet-5@default | 48/48 | 0/48 |
| google/gemini-3-flash-preview | 48/48 | 0/48 |
| google/gemini-3.1-flash-lite-preview | 37/48 | 6/37 |
| openai/gpt-5.4-nano-2026-03-17 | 12/48 | 4/12 |

## Calibration (all conditions)

Primary: answers that commit to a number (kind `number`). Secondary: all scored answers.

| model | arm | n_number | acc_number | mean_conf_number | brier_number | ece_number | n_all | brier_all | ece_all |
|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | BASE | 206 | 70% | 77 | 0.052 | 0.108 | 240 | 0.132 | 0.150 |
| anthropic/claude-sonnet-5@default | PERMIT | 48 | 98% | 89 | 0.031 | 0.092 | 96 | 0.442 | 0.505 |
| google/gemini-3-flash-preview | BASE | 202 | 71% | 98 | 0.252 | 0.265 | 240 | 0.346 | 0.357 |
| google/gemini-3-flash-preview | PERMIT | 31 | 100% | 98 | 0.001 | 0.015 | 96 | 0.177 | 0.172 |
| google/gemini-3.1-flash-lite-preview | BASE | 499 | 55% | 96 | 0.396 | 0.406 | 528 | 0.425 | 0.435 |
| google/gemini-3.1-flash-lite-preview | PERMIT | 414 | 60% | 95 | 0.341 | 0.353 | 528 | 0.354 | 0.364 |
| openai/gpt-5.4-nano-2026-03-17 | BASE | 506 | 32% | 84 | 0.456 | 0.524 | 528 | 0.455 | 0.492 |
| openai/gpt-5.4-nano-2026-03-17 | PERMIT | 424 | 37% | 92 | 0.514 | 0.557 | 528 | 0.484 | 0.515 |

Always-abstain baseline accuracy on the BASE item set: 36%.

## Cost

| model | arm | rows | cost | in_tok | out_tok | per_row | main_rows | main_projection |
|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | BASE | 240 | $1.3923 | 1174 | 345 | $0.0058 | 528 | $3.0630 |
| anthropic/claude-sonnet-5@default | PERMIT | 96 | $0.3477 | 1202 | 122 | $0.0036 | 528 | $1.9121 |
| anthropic/claude-sonnet-5@default | PROBE | 48 | $0.1435 | 1227 | 54 | $0.0030 | 528 | $1.5785 |
| anthropic/claude-sonnet-5@default | SUMCAP | 48 | $0.1569 | 1210 | 85 | $0.0033 | 48 | $0.1569 |
| anthropic/claude-sonnet-5@default | TWOPASS | 96 | $0.5242 | 2585 | 121 | $0.0055 | 192 | $1.0484 |
| google/gemini-3-flash-preview | BASE | 240 | $1.3452 | 1152 | 1676 | $0.0056 | 528 | $2.9595 |
| google/gemini-3-flash-preview | PERMIT | 96 | $0.4182 | 1173 | 1256 | $0.0044 | 528 | $2.3001 |
| google/gemini-3-flash-preview | PROBE | 48 | $0.0672 | 1177 | 270 | $0.0014 | 528 | $0.7389 |
| google/gemini-3-flash-preview | SUMCAP | 48 | $0.1094 | 1168 | 565 | $0.0023 | 48 | $0.1094 |
| google/gemini-3-flash-preview | TWOPASS | 96 | $0.3945 | 2466 | 959 | $0.0041 | 192 | $0.7891 |
| google/gemini-3.1-flash-lite-preview | BASE | 528 | $0.1701 | 1152 | 23 | $0.0003 | 528 | $0.1701 |
| google/gemini-3.1-flash-lite-preview | PERMIT | 528 | $0.1725 | 1173 | 22 | $0.0003 | 528 | $0.1725 |
| google/gemini-3.1-flash-lite-preview | PROBE | 528 | $0.1783 | 1177 | 29 | $0.0003 | 528 | $0.1783 |
| google/gemini-3.1-flash-lite-preview | SUMCAP | 48 | $0.0159 | 1168 | 26 | $0.0003 | 48 | $0.0159 |
| google/gemini-3.1-flash-lite-preview | TWOPASS | 192 | $0.1318 | 2466 | 47 | $0.0007 | 192 | $0.1318 |
| openai/gpt-5.4-nano-2026-03-17 | BASE | 528 | $0.1049 | 876 | 19 | $0.0002 | 528 | $0.1049 |
| openai/gpt-5.4-nano-2026-03-17 | PERMIT | 528 | $0.1071 | 897 | 19 | $0.0002 | 528 | $0.1071 |
| openai/gpt-5.4-nano-2026-03-17 | PROBE | 528 | $0.1108 | 893 | 25 | $0.0002 | 528 | $0.1108 |
| openai/gpt-5.4-nano-2026-03-17 | SUMCAP | 48 | $0.0097 | 893 | 20 | $0.0002 | 48 | $0.0097 |
| openai/gpt-5.4-nano-2026-03-17 | TWOPASS | 192 | $0.0834 | 1905 | 43 | $0.0004 | 192 | $0.0834 |

Projected main-run cost per model: anthropic/claude-sonnet-5@default: $7.76, google/gemini-3-flash-preview: $6.90, google/gemini-3.1-flash-lite-preview: $0.67, openai/gpt-5.4-nano-2026-03-17: $0.42