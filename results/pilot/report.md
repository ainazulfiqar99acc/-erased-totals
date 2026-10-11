# pilot results

## Hypotheses (descriptive only on the pilot split; not evidence)

- NOT SUPPORTED — H1 N100×BASE macro invention ≥40% and median confidence of inventions ≥70: 47% [28–69]; median conf 55.0
- NOT SUPPORTED — H2 D100×BASE macro derivation failure ≥30%: 28% [19–33]
- SUPPORTED — S4 N50 invention > N100 invention (bootstrap lower bound > 0): +53 pts [31–72]
- SUPPORTED — S1 knows-vs-does: macro invention despite correct PROBE ≥25%: 47%
- SUPPORTED — S2 TWOPASS cuts N100 invention ≥10 pts vs PERMIT, D100 accuracy within 5 pts: invention 11%→0%; D100 acc 61%→67%

## Pilot gate checks

- PASS — G3 errors ≤10% per model×arm
- PASS — G1 V1 (clean ≥90%) passes for ≥2 of 3 models
- PASS — G2 V3 leak ≤5%
- PASS — G4 non-trivial effect (N100 invention ≥15% or D100 failure ≥10%)
- PASS — G5 projected main cost ≤ $10 per model

**Overall: GO**

## Errors (V4)

| model | arm | n | ok | format_error | api_error | error_rate |
|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | BASE | 72 | 72 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | PERMIT | 72 | 72 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | PROBE | 72 | 72 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | SUMCAP | 12 | 12 | 0 | 0 | 0% |
| anthropic/claude-sonnet-5@default | TWOPASS | 24 | 24 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | BASE | 72 | 72 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | PERMIT | 72 | 72 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | PROBE | 72 | 72 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | SUMCAP | 12 | 12 | 0 | 0 | 0% |
| google/gemini-3-flash-preview | TWOPASS | 24 | 24 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | BASE | 72 | 72 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | PERMIT | 72 | 72 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | PROBE | 72 | 72 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | SUMCAP | 12 | 12 | 0 | 0 | 0% |
| openai/gpt-5.4-nano-2026-03-17 | TWOPASS | 24 | 24 | 0 | 0 | 0% |

## Accuracy by condition (correct / scored)

**BASE**

| model | clean | D0 | D50 | D100 | N50 | N100 |
|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 | 12/12 | 12/12 | 12/12 | 0/12 | 3/12 |
| google/gemini-3-flash-preview | 12/12 | 12/12 | 12/12 | 12/12 | 0/12 | 9/12 |
| openai/gpt-5.4-nano-2026-03-17 | 12/12 | 12/12 | 1/12 | 2/12 | 0/12 | 4/12 |

**PERMIT**

| model | clean | D0 | D50 | D100 | N50 | N100 |
|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 | 12/12 | 11/12 | 11/12 | 4/12 | 11/12 |
| google/gemini-3-flash-preview | 12/12 | 12/12 | 12/12 | 9/12 | 11/12 | 12/12 |
| openai/gpt-5.4-nano-2026-03-17 | 12/12 | 12/12 | 1/12 | 2/12 | 2/12 | 9/12 |

**TWOPASS**

| model | D100 | N100 |
|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 | 12/12 |
| google/gemini-3-flash-preview | 12/12 | 12/12 |
| openai/gpt-5.4-nano-2026-03-17 | 0/12 | 12/12 |

**SUMCAP**

| model | D100 |
|---|---|
| anthropic/claude-sonnet-5@default | 12/12 |
| google/gemini-3-flash-preview | 12/12 |
| openai/gpt-5.4-nano-2026-03-17 | 2/12 |

## Answer kinds (number / hedged / abstain) on occluded totals

| arm | model | condition | number | hedged_number | abstain |
|---|---|---|---|---|---|
| BASE | anthropic/claude-sonnet-5@default | D100 | 12 | 0 | 0 |
| BASE | anthropic/claude-sonnet-5@default | D50 | 12 | 0 | 0 |
| BASE | anthropic/claude-sonnet-5@default | N100 | 6 | 3 | 3 |
| BASE | anthropic/claude-sonnet-5@default | N50 | 12 | 0 | 0 |
| BASE | google/gemini-3-flash-preview | D100 | 12 | 0 | 0 |
| BASE | google/gemini-3-flash-preview | D50 | 12 | 0 | 0 |
| BASE | google/gemini-3-flash-preview | N100 | 3 | 0 | 9 |
| BASE | google/gemini-3-flash-preview | N50 | 12 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | D100 | 10 | 0 | 2 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | D50 | 12 | 0 | 0 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | N100 | 8 | 0 | 4 |
| BASE | openai/gpt-5.4-nano-2026-03-17 | N50 | 12 | 0 | 0 |
| PERMIT | anthropic/claude-sonnet-5@default | D100 | 12 | 0 | 0 |
| PERMIT | anthropic/claude-sonnet-5@default | D50 | 12 | 0 | 0 |
| PERMIT | anthropic/claude-sonnet-5@default | N100 | 1 | 0 | 11 |
| PERMIT | anthropic/claude-sonnet-5@default | N50 | 8 | 0 | 4 |
| PERMIT | google/gemini-3-flash-preview | D100 | 9 | 0 | 3 |
| PERMIT | google/gemini-3-flash-preview | D50 | 12 | 0 | 0 |
| PERMIT | google/gemini-3-flash-preview | N100 | 0 | 0 | 12 |
| PERMIT | google/gemini-3-flash-preview | N50 | 1 | 0 | 11 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | D100 | 6 | 0 | 6 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | D50 | 11 | 0 | 1 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | N100 | 3 | 0 | 9 |
| PERMIT | openai/gpt-5.4-nano-2026-03-17 | N50 | 10 | 0 | 2 |
| TWOPASS | anthropic/claude-sonnet-5@default | D100 | 12 | 0 | 0 |
| TWOPASS | anthropic/claude-sonnet-5@default | N100 | 0 | 0 | 12 |
| TWOPASS | google/gemini-3-flash-preview | D100 | 12 | 0 | 0 |
| TWOPASS | google/gemini-3-flash-preview | N100 | 0 | 0 | 12 |
| TWOPASS | openai/gpt-5.4-nano-2026-03-17 | D100 | 0 | 0 | 12 |
| TWOPASS | openai/gpt-5.4-nano-2026-03-17 | N100 | 0 | 0 | 12 |

## Validity checks

| model | clean_acc | V1_pass | flagged_lt80 | D0_acc | V2_pass |
|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 = 100% [76–100] | True | False | 12/12 = 100% [76–100] | True |
| google/gemini-3-flash-preview | 12/12 = 100% [76–100] | True | False | 12/12 = 100% [76–100] | True |
| openai/gpt-5.4-nano-2026-03-17 | 12/12 = 100% [76–100] | True | False | 12/12 = 100% [76–100] | True |

**V3 leak:** 0/76 number answers on N50–N100 equal the true total (0%). Pass = ≤5%.

**Fragment reads** (answer = the visible part of a partly covered total): 33/144.

## H1 — invention on N100 × BASE (strict)

| model | invention | lenient | median_conf_invented |
|---|---|---|---|
| anthropic/claude-sonnet-5@default | 6/12 = 50% [25–75] | 9/12 = 75% [47–91] | 20 |
| google/gemini-3-flash-preview | 3/12 = 25% [9–53] | 3/12 = 25% [9–53] | 95 |
| openai/gpt-5.4-nano-2026-03-17 | 8/12 = 67% [39–86] | 8/12 = 67% [39–86] | 62 |

Macro invention = 47% [28–69] (threshold 40%); median confidence of invented answers (pooled over included models) = 55.0 (threshold 70).

## H2 — derivation failure on D100 × BASE

| model | failure | abstained | wrong_number | hedged |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 0/12 = 0% [0–24] | 0 | 0 | 0 |
| google/gemini-3-flash-preview | 0/12 = 0% [0–24] | 0 | 0 | 0 |
| openai/gpt-5.4-nano-2026-03-17 | 10/12 = 83% [55–95] | 2 | 8 | 0 |

Macro derivation failure = 28% [19–33] (threshold 30%).

## S4 — partial erasure: N50 vs N100 invention (BASE, strict)

| model | N50_invention | N100_invention |
|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 = 100% [76–100] | 6/12 = 50% [25–75] |
| google/gemini-3-flash-preview | 12/12 = 100% [76–100] | 3/12 = 25% [9–53] |
| openai/gpt-5.4-nano-2026-03-17 | 12/12 = 100% [76–100] | 8/12 = 67% [39–86] |

Macro N50 − N100 = +53 points [31–72]. Supported if > 0 and lower bound > 0.

## S1 — knows vs does (N100)

| model | probe_says_hidden_and_not_computable | of_those_BASE_invents |
|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 | 6/12 = 50% [25–75] |
| google/gemini-3-flash-preview | 12/12 | 3/12 = 25% [9–53] |
| openai/gpt-5.4-nano-2026-03-17 | 12/12 | 8/12 = 67% [39–86] |

Macro BASE invention among items the model's own PROBE calls hidden and not computable = 47% (threshold 25%).

**PROBE answers by condition** (said visible / said computable):

| model | condition | said_visible | said_computable | n |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | D0 | 12 | 12 | 12 |
| anthropic/claude-sonnet-5@default | D100 | 0 | 12 | 12 |
| anthropic/claude-sonnet-5@default | D50 | 0 | 12 | 12 |
| anthropic/claude-sonnet-5@default | N100 | 0 | 0 | 12 |
| anthropic/claude-sonnet-5@default | N50 | 0 | 0 | 12 |
| anthropic/claude-sonnet-5@default | clean | 12 | 12 | 12 |
| google/gemini-3-flash-preview | D0 | 12 | 12 | 12 |
| google/gemini-3-flash-preview | D100 | 0 | 12 | 12 |
| google/gemini-3-flash-preview | D50 | 0 | 12 | 12 |
| google/gemini-3-flash-preview | N100 | 0 | 0 | 12 |
| google/gemini-3-flash-preview | N50 | 0 | 0 | 12 |
| google/gemini-3-flash-preview | clean | 12 | 12 | 12 |
| openai/gpt-5.4-nano-2026-03-17 | D0 | 12 | 6 | 12 |
| openai/gpt-5.4-nano-2026-03-17 | D100 | 0 | 2 | 12 |
| openai/gpt-5.4-nano-2026-03-17 | D50 | 2 | 4 | 12 |
| openai/gpt-5.4-nano-2026-03-17 | N100 | 0 | 0 | 12 |
| openai/gpt-5.4-nano-2026-03-17 | N50 | 0 | 0 | 12 |
| openai/gpt-5.4-nano-2026-03-17 | clean | 12 | 5 | 12 |

## S2 — fixes on N100 / D100

| model | BASE N100 invent | BASE D100 acc | PERMIT N100 invent | PERMIT D100 acc | TWOPASS N100 invent | TWOPASS D100 acc |
|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 6/12 = 50% [25–75] | 12/12 = 100% [76–100] | 1/12 = 8% [1–35] | 11/12 = 92% [65–99] | 0/12 = 0% [0–24] | 12/12 = 100% [76–100] |
| google/gemini-3-flash-preview | 3/12 = 25% [9–53] | 12/12 = 100% [76–100] | 0/12 = 0% [0–24] | 9/12 = 75% [47–91] | 0/12 = 0% [0–24] | 12/12 = 100% [76–100] |
| openai/gpt-5.4-nano-2026-03-17 | 8/12 = 67% [39–86] | 2/12 = 17% [5–45] | 3/12 = 25% [9–53] | 2/12 = 17% [5–45] | 0/12 = 0% [0–24] | 0/12 = 0% [0–24] |

Macro N100 invention: PERMIT 11% → TWOPASS 0% (needs ≥10 points lower). Macro D100 accuracy: PERMIT 61% → TWOPASS 67% (may drop ≤5 points).

## S3 — capacity vs policy (D100)

| model | SUMCAP_correct | could_but_BASE_failed |
|---|---|---|
| anthropic/claude-sonnet-5@default | 12/12 | 0/12 |
| google/gemini-3-flash-preview | 12/12 | 0/12 |
| openai/gpt-5.4-nano-2026-03-17 | 2/12 | 0/2 |

## Calibration (all conditions)

Primary: answers that commit to a number (kind `number`). Secondary: all scored answers.

| model | arm | n_number | acc_number | mean_conf_number | brier_number | ece_number | n_all | brier_all | ece_all |
|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | BASE | 66 | 73% | 78 | 0.046 | 0.133 | 72 | 0.077 | 0.137 |
| anthropic/claude-sonnet-5@default | PERMIT | 57 | 81% | 85 | 0.060 | 0.074 | 72 | 0.233 | 0.249 |
| google/gemini-3-flash-preview | BASE | 63 | 76% | 98 | 0.206 | 0.217 | 72 | 0.278 | 0.287 |
| google/gemini-3-flash-preview | PERMIT | 46 | 98% | 100 | 0.020 | 0.017 | 72 | 0.110 | 0.108 |
| openai/gpt-5.4-nano-2026-03-17 | BASE | 66 | 41% | 86 | 0.389 | 0.451 | 72 | 0.389 | 0.418 |
| openai/gpt-5.4-nano-2026-03-17 | PERMIT | 54 | 50% | 94 | 0.422 | 0.440 | 72 | 0.395 | 0.406 |

Always-abstain baseline accuracy on the BASE item set: 33%.

## Cost

| model | arm | rows | cost | in_tok | out_tok | per_row | main_rows | main_projection |
|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | BASE | 72 | $0.4280 | 1186 | 357 | $0.0059 | 528 | $3.1386 |
| anthropic/claude-sonnet-5@default | PERMIT | 72 | $0.3205 | 1214 | 202 | $0.0045 | 528 | $2.3500 |
| anthropic/claude-sonnet-5@default | PROBE | 72 | $0.2472 | 1239 | 95 | $0.0034 | 528 | $1.8126 |
| anthropic/claude-sonnet-5@default | SUMCAP | 12 | $0.0417 | 1222 | 103 | $0.0035 | 48 | $0.1667 |
| anthropic/claude-sonnet-5@default | TWOPASS | 24 | $0.1116 | 2610 | 121 | $0.0047 | 192 | $0.8928 |
| google/gemini-3-flash-preview | BASE | 72 | $0.3781 | 1151 | 1559 | $0.0053 | 528 | $2.7729 |
| google/gemini-3-flash-preview | PERMIT | 72 | $0.2611 | 1172 | 1013 | $0.0036 | 528 | $1.9144 |
| google/gemini-3-flash-preview | PROBE | 72 | $0.1222 | 1176 | 370 | $0.0017 | 528 | $0.8964 |
| google/gemini-3-flash-preview | SUMCAP | 12 | $0.0251 | 1167 | 502 | $0.0021 | 48 | $0.1004 |
| google/gemini-3-flash-preview | TWOPASS | 24 | $0.0955 | 2464 | 916 | $0.0040 | 192 | $0.7641 |
| openai/gpt-5.4-nano-2026-03-17 | BASE | 72 | $0.0144 | 883 | 19 | $0.0002 | 528 | $0.1055 |
| openai/gpt-5.4-nano-2026-03-17 | PERMIT | 72 | $0.0147 | 904 | 18 | $0.0002 | 528 | $0.1076 |
| openai/gpt-5.4-nano-2026-03-17 | PROBE | 72 | $0.0152 | 900 | 25 | $0.0002 | 528 | $0.1115 |
| openai/gpt-5.4-nano-2026-03-17 | SUMCAP | 12 | $0.0025 | 900 | 20 | $0.0002 | 48 | $0.0098 |
| openai/gpt-5.4-nano-2026-03-17 | TWOPASS | 24 | $0.0105 | 1917 | 43 | $0.0004 | 192 | $0.0839 |

Projected main-run cost per model: anthropic/claude-sonnet-5@default: $8.36, google/gemini-3-flash-preview: $6.45, openai/gpt-5.4-nano-2026-03-17: $0.42