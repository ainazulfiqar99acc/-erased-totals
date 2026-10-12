---
title: "We taped over the total. Vision models filled it in anyway."
published: false
tags: devchallenge, kagglechallenge, ai, llm
cover_image: https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/video/slides/01_title.png
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

## What I Benchmarked

Here is a receipt. One line item and half of the total are covered with tape. The right answer to "what is the total?" is **"I can't tell"**: the visible digits `.61` don't pin down the rest, and the line items can't be added up because one of them is hidden.

I asked four vision models. **Four different totals came back, all ending in `.61`**, three of them at confidence 92–100:

![Four models, four made-up totals](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/card_four_answers.png)

The true total was 255.61. Gemini 3 Flash's 230.61 is exactly the visible lines (211.03) plus a made-up 19.58 for the hidden line, picked so the result ends in `.61`.

**2-minute video walkthrough:**

{% youtube LA2v5tQWcqg %}

**The behaviour I measured:** when the number you ask for is physically covered, does a vision model say it can't tell, or make one up? And when it *can* be worked out from what's visible, does it do the sum? Bills and receipts get shared as phone photos with a thumb, fold or sticker over part of the page, then pasted into an assistant: "what do I owe?" A confident made-up total there is a plausible, wrong number with no warning attached.

**Stimuli.** A seeded renderer draws generic bills (retail receipts, restaurant bills, utility bills, service invoices, lab invoices, fee statements; fictional issuers; USD/EUR/GBP/CAD/AUD/CHF). Every amount is generated in code, so the answer key is exact and nothing is hand-typed. There is no subtotal, tax rate, unit price or "amount paid" line, so the only way to the total is the total itself or the sum of the line items.

| Code | What is taped | Correct answer |
|---|---|---|
| `clean` | nothing | the total |
| `D0` | an irrelevant field (placebo) | the total |
| `D100` | the whole total | the total (add the lines) |
| `N50` | half the total + one line item | "can't tell" |
| `N100` | the whole total + one line item | "can't tell" |

`D` and `N` are twins: the same page with the same tape on the total, differing only in where the second piece of tape sits. 48 bills per condition.

![Same bill, four versions](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/card_design.png)

**Prompts.** The plain prompt asks for the total and a 0–100 confidence; the answer field is free text, so "not visible" is easy to say. I also tested a separate probe ("is the total visible? can it be computed from the visible amounts?"), a "you may say UNREADABLE" version, and a two-step version (probe first, then extract, in the same chat).

**Rigour.** Hypotheses, thresholds and analysis were preregistered before any model call. A 12-bill pilot was run on separate bills first, and every later change is logged as a dated deviation. Scoring is deterministic regex, with no LLM judge. Confidence intervals are a cluster bootstrap over bills.

## Models Tested

- **Claude Sonnet 5** (Anthropic)
- **Gemini 3 Flash** (Google)
- **Gemini 3.1 Flash-Lite** (Google)
- **GPT-5.4 nano** (OpenAI)

These are the vision-capable models on the Kaggle Benchmarks model proxy that passed a one-image check (the others are text-only). Together they cover three labs and a range from small to frontier-class. All were run through `kaggle-benchmarks` with provider defaults, one sample per image, ≤ 4 parallel requests.

**Sanity checks:**
- All four read every clean bill (48/48) and every placebo bill (48/48), so the images are legible.
- Of 521 made-up numbers, **0** equalled the hidden total, so nothing on the page leaks it.
- 0 errors across 4,704 scored responses.

## Findings

### 1. Half a total is worse than no total

![Answers when the total cannot be known](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/invention.png)

| Model | Total fully taped: makes one up | Total half taped: makes one up |
|---|---|---|
| Claude Sonnet 5 | 38% | 92% |
| Gemini 3 Flash | 21% | 100% |
| Gemini 3.1 Flash-Lite | 44% | 100% |
| GPT-5.4 nano | 73% | 100% |

Preregistered H1 (≥ 40% made-up totals on fully taped, non-computable bills, at median confidence ≥ 70) was **supported**: 44% [35–52], median confidence 85. The half-taped effect (added after the pilot and tested only on fresh bills) was **supported**: +54 points [46–62].

Visible digits act as an anchor. 98% of Claude's and Gemini 3 Flash's half-taped answers kept the visible digits. About a quarter just reported the visible fragment as the total, and the rest invented the hidden digits around it.

### 2. "Confidently" depends on the model

![Confidence of made-up totals](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/confidence.png)

Median stated confidence on made-up totals (total fully taped): **Gemini 3 Flash 95, Gemini 3.1 Flash-Lite 95**, GPT-5.4 nano 62, **Claude Sonnet 5 20**. Claude guesses, but it says it's guessing. Across all committed numbers, Gemini 3 Flash averaged 98 confidence at 71% accuracy, while Claude averaged 77 at 70% (the best calibrated).

### 3. They know, and answer anyway

![Gemini 3 Flash says the total is hidden, then gives one](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/card_knows_vs_does.png)

![Knows vs does](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/knows_vs_does.png)

Asked separately, Claude, Gemini 3 Flash and Flash-Lite said on **48 of 48** bills that the total is *not visible* and *not computable*. On those same bills, the plain question still got a made-up total 21–44% of the time (nano: 71% of the 42 it flagged). The failure isn't perception: the model can tell the information is gone, and "answer the question" wins anyway.

### 4. Doing the sum is a capacity problem, not a habit

When the total is taped but every line is visible, Claude and Gemini 3 Flash **worked it out 48/48 times**. Failures came from the smaller models (Flash-Lite 31%, nano 79%). Nano also fails when told outright to add the lines (12/48 correct), so that is arithmetic, not a policy. Preregistered H2 (≥ 30% failure) was **not supported** (28% [22–33]).

### 5. The fix: check first, then answer

![Fixes](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/fix.png)

- **"You may say UNREADABLE"** removes made-up totals for Claude and Gemini 3 Flash (0/48), but Gemini 3 Flash then gives up on a third of totals it *could* compute (65% vs 100%).
- **Check first, then answer** (probe, then extract, in the same chat) keeps made-up totals at **0–2%** for every model, and Gemini 3 Flash computes recoverable totals again (98%).

My preregistered comparison required two-step to beat "you may say UNREADABLE" by ≥ 10 more points on made-up totals. It didn't, because the permission alone already brought the big models to 0%. The two-step version's real win is that it doesn't make models give up on totals they can compute.

### 6. Real receipts: worse, not better

To check this isn't an artefact of clean synthetic bills, I also ran **30 real receipt photos** from CORD, a public dataset of photographed receipts (CC-BY 4.0), using the dataset's own labels as the answer key. I used only receipts whose labels prove the total can be worked out from the line items, and taped the amounts (not the labels) the same way. This part is exploratory, with a small sample.

![A real receipt with the total taped](https://raw.githubusercontent.com/ainazulfiqar99acc/-erased-totals/main/docs/figures/card_real_receipt.png)

| Model | Reads the clean receipt | Total can't be known: makes one up | Median confidence | Its own probe: "hidden, not computable" |
|---|---|---|---|---|
| Claude Sonnet 5 | 29/30 | 12/30 (40%) | 22 | 30/30 |
| Gemini 3 Flash | 29/30 | **22/30 (73%)** | **95** | 30/30 |
| Gemini 3.1 Flash-Lite | 29/30 | 17/30 (57%) | 95 | 29/30 |
| GPT-5.4 nano | 20/30 | 23/30 (77%) | 35 | 30/30 |

- **Gemini 3 Flash went from 21% made-up totals on synthetic bills to 73% on real ones**, still at confidence 95, while its own probe said 30/30 times that the total was hidden and not computable.
- **Check-first still works on real photos.** Made-up totals dropped to 2/30 (Claude), 1/30 (Flash-Lite) and 0/30 (nano). Claude and Flash-Lite still worked out recoverable totals (29/30, 28/30). Gemini 3 Flash's check-first run on real receipts didn't fit in the day's quota.
- 3 of 77 made-up numbers matched the hidden total exactly, all from Gemini 3 Flash and all round amounts (e.g. 40.000). That's under my 5% leak threshold, but a reminder that real receipts can carry hints I didn't tape.
- Nano can't reliably read these photos (20/30 clean), so its row is weak evidence.

### What surprised me

- Partial erasure is the trap. A fully hidden total often gets "I can't tell"; leave part of it visible and every model fills in the rest.
- The models *knew*. The separate probe was right 48/48 times for Claude, Gemini 3 Flash and Flash-Lite (42/48 for nano), yet the plain question still produced a made-up number. Asking the model to check first was enough to fix it.
- Confidence tracked the model, not the evidence: 95 from Gemini on a number it couldn't see, 20 from Claude on the same kind of guess.

### Limits

- Synthetic bills are simple on purpose (that's what makes "can't tell" provably correct), so real bills are likely harder, not easier. The real-receipt check points the same way.
- Single sample per item; provider-default temperature.
- Because of the deadline, Claude Sonnet 5 and Gemini 3 Flash were run on the core conditions above. The extra tape levels (25/50/75%) were run only for the two smaller models. That was logged before those runs, and no hypothesis uses those levels.
- Prior work (#167) showed a text model inventing a total when a page was missing. This adds the vision setting, the tape-dose ladder and the computable/not-computable twins.

### What I'd measure next

- The full tape-dose ladder (25/50/75%) for the two big models, and test–retest with repeated samples.
- Physically taped, printed bills photographed on a phone.
- Other fields that get covered in real life: dates, account numbers, quantities.

**Takeaway:** if you build on vision models for bills, receipts or invoices, **ask whether the value is visible before asking for the value.** It's one extra turn, and in this test it took made-up totals from up to 73% down to 0–2% (on real receipts, from up to 77% down to 0–7%), without making the strong models give up on totals they could compute.

## My Benchmark

- **Kaggle benchmark:** [Erased Totals on Kaggle](https://www.kaggle.com/benchmarks/tasks/ainazu/erased-totals/4). 96 bill photos (24 bills × clean / derivable / half-taped / fully taped), scored as the share answered correctly, where "can't tell" is the correct answer on the bills whose total can't be worked out.
- **Video walkthrough (2 min):** https://youtu.be/LA2v5tQWcqg
- **Full study:** preregistration, deviation log, renderer, runner, scoring, all raw model responses and the real-receipt add-on: https://github.com/ainazulfiqar99acc/-erased-totals
