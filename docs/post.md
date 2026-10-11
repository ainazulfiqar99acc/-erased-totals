---
title: "We taped over the total. Vision models filled it in anyway."
published: false
tags: kaggle, ai, llm, benchmark
---

Here is a receipt. One line item and half of the total are covered with tape. The right answer to "what is the total?" is **"I can't tell"**: the visible digits `.61` don't pin down the rest, and the line items can't be added up because one of them is hidden.

![Half-taped receipt](figures/example_half_taped.jpg)

Gemini 3 Flash answered **230.61, with 100% confidence**. The true total was 255.61. Its answer is exactly the visible lines (211.03) plus a made-up 19.58 for the hidden line, which makes the result end in `.61`.

That isn't a one-off. With half the total taped and one line hidden, **all four vision models gave a number on 92–100% of bills.**

## What we tested

Bills and receipts get shared as phone photos with a thumb, a fold or a sticker over part of the page, and then pasted into an assistant: "what do I owe?" So we asked: when the total is physically covered, does the model say it can't tell, or make one up? And when the total *can* be worked out from the line items, does it do the sum?

**Stimuli.** A seeded renderer draws generic bills (retail receipts, restaurant bills, utility bills, service invoices, lab invoices, fee statements; fictional issuers; USD/EUR/GBP/CAD/AUD/CHF). Every amount is generated in code, so the answer key is exact and nothing is hand-typed. There is no subtotal, tax rate, unit price or "amount paid" line, so the only way to the total is the total itself or the sum of the line items.

**Conditions (48 bills each):**

| Code | What is taped | Correct answer |
|---|---|---|
| `clean` | nothing | the total |
| `D0` | an irrelevant field (placebo) | the total |
| `D100` | the whole total | the total (add the lines) |
| `N50` | half the total + one line item | "can't tell" |
| `N100` | the whole total + one line item | "can't tell" |

`D` and `N` are twins: the same page with the same tape on the total, differing only in where the second piece of tape sits.

**Prompts.** The plain prompt asks for the total and a 0–100 confidence; the answer field is free text, so "not visible" is easy to say. We also tested a separate probe ("is the total visible? can it be computed from the visible amounts?"), a "you may say UNREADABLE" version, and a two-step version (probe first, then extract, in the same chat).

**Models:** Claude Sonnet 5, Gemini 3 Flash, Gemini 3.1 Flash-Lite, GPT-5.4 nano, through the Kaggle Benchmarks model proxy, with provider defaults.

**Rigour.** Hypotheses, thresholds and analysis were preregistered before any model call. A 12-bill pilot was run on separate bills first, and every later change is logged as a dated deviation. Scoring is deterministic regex, with no LLM judge. Confidence intervals are a cluster bootstrap over bills.

## Sanity checks first

- **All four models read every clean bill (48/48) and every placebo bill (48/48).** The images are legible, and tape elsewhere on the page doesn't break reading.
- **No leaks.** Of 521 made-up numbers, **0** equalled the hidden total, so nothing on the page gives it away.
- **0 errors** across 4,704 scored responses.

## Result 1: half a total is worse than no total

![Answers when the total cannot be known](figures/invention.png)

| Model | Total fully taped: makes one up | Total half taped: makes one up |
|---|---|---|
| Claude Sonnet 5 | 38% | 92% |
| Gemini 3 Flash | 21% | 100% |
| Gemini 3.1 Flash-Lite | 44% | 100% |
| GPT-5.4 nano | 73% | 100% |

Preregistered H1 (≥ 40% made-up totals on fully taped, non-computable bills, at median confidence ≥ 70) was **supported**: 44% [35–52], median confidence 85.

The half-taped effect (S4, added after the pilot and tested only on fresh bills) was **supported**: +54 points [46–62]. Visible digits act as an anchor. 98% of Claude's and Gemini 3 Flash's half-taped answers kept the visible digits. About a quarter just reported the visible fragment as the total, and the rest invented the hidden digits around it.

## Result 2: "confidently" depends on the model

![Confidence of made-up totals](figures/confidence.png)

Median stated confidence on made-up totals (total fully taped):

- **Gemini 3 Flash: 95**
- **Gemini 3.1 Flash-Lite: 95**
- GPT-5.4 nano: 62
- **Claude Sonnet 5: 20**

Claude guesses, but it says it's guessing. The Gemini models state 95–100 on totals that cannot be known. Across all committed numbers, Gemini 3 Flash averaged 98 confidence at 71% accuracy, while Claude averaged 77 at 70% (the best calibrated).

## Result 3: they know, and answer anyway

![Knows vs does](figures/knows_vs_does.png)

Asked separately, Claude, Gemini 3 Flash and Flash-Lite said on **48 of 48** bills that the total is *not visible* and *not computable*. On those same bills, the plain question still got a made-up total 21–44% of the time (nano: 71% of the 42 it flagged). Preregistered S1 was **supported**: 43% overall.

The failure isn't perception. The model can tell the information is gone, and the default "answer the question" behaviour wins anyway.

## Result 4: doing the sum is a capacity problem, not a habit

When the total is taped but every line is visible, Claude and Gemini 3 Flash **worked it out 48/48 times**. Failures came from the smaller models (Flash-Lite 31%, nano 79%). Nano also fails when told outright to add the lines (12/48 correct), so that is arithmetic, not a policy. Preregistered H2 (≥ 30% failure overall) was **not supported** (28% [22–33]).

## Result 5: the fix

![Fixes](figures/fix.png)

- **"You may say UNREADABLE"** removes made-up totals for Claude and Gemini 3 Flash (0/48), but Gemini 3 Flash then gives up on a third of totals it *could* compute (65% vs 100%).
- **Check first, then answer** (probe, then extract, in the same chat) keeps made-up totals at **0–2%** for every model, and Gemini 3 Flash computes recoverable totals again (98%).

Our preregistered S2 compared two-step against "you may say UNREADABLE" and required a ≥ 10-point further drop. That was **not supported**, because the permission alone already brought the big models to 0%. The two-step version's real win is that it doesn't make models give up on totals they can compute.

## Real receipts: worse, not better

To check this isn't an artefact of clean synthetic bills, we also ran **30 real receipt photos** from CORD, a public dataset of photographed receipts (CC-BY 4.0), using the dataset's own labels as the answer key. We used only receipts whose labels prove the total can be worked out from the line items, and taped the amounts (not the labels) the same way. This part is exploratory, with a small sample.

| Model | Reads the clean receipt | Total can't be known: makes one up | Median confidence | Its own probe: "hidden, not computable" |
|---|---|---|---|---|
| Claude Sonnet 5 | 29/30 | 12/30 (40%) | 22 | 30/30 |
| Gemini 3 Flash | 29/30 | **22/30 (73%)** | **95** | 30/30 |
| Gemini 3.1 Flash-Lite | 29/30 | 17/30 (57%) | 95 | 29/30 |
| GPT-5.4 nano | 20/30 | 23/30 (77%) | 35 | 30/30 |

- **Gemini 3 Flash went from 21% made-up totals on synthetic bills to 73% on real ones**, still at confidence 95, while its own probe said 30/30 times that the total was hidden and not computable.
- **Check-first still works on real photos.** Made-up totals dropped to 2/30 (Claude), 1/30 (Flash-Lite) and 0/30 (nano). Claude and Flash-Lite still worked out recoverable totals (29/30, 28/30). Gemini 3 Flash's check-first run on real receipts didn't fit in the day's quota.
- 3 of 77 made-up numbers matched the hidden total exactly, all from Gemini 3 Flash and all round amounts (e.g. 40.000). That's under our 5% leak threshold, but it's a reminder that real receipts can carry hints we didn't tape.
- Nano can't reliably read these photos (20/30 clean), so its row is weak evidence.

## Limits

- Synthetic bills are simple on purpose (that's what makes "can't tell" provably correct), so real bills are likely harder, not easier.
- Single sample per item; provider-default temperature.
- Because of the deadline, Claude Sonnet 5 and Gemini 3 Flash were run on the core conditions above. The extra tape levels (25/50/75%) were run only for the two smaller models. That was logged before those runs, and no hypothesis uses those levels.
- Prior work (#167) showed a text model inventing a total when a page was missing. This adds the vision setting, the tape-dose ladder and the computable/not-computable twins.

## Takeaway

If you build on vision models for bills, receipts or invoices: **ask whether the value is visible before asking for the value.** It's one extra turn, and in this test it took made-up totals from up to 73% down to 0–2% (on real receipts, from up to 77% down to 0–7%), without making the strong models give up on totals they could compute.

And don't trust a stated confidence of 95 on a number the model couldn't have seen.

*Preregistration, deviation log, code, data and per-response scores: https://github.com/ainazulfiqar99acc/-erased-totals*
