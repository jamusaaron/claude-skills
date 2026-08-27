# Cognitive bias checklist for researchers

Run this **after gather** and again **before deliver**. Bias is not a personality flaw; it is the default. The workflow exists to make the defaults expensive.

## Selection & search

| Bias | How it shows up | Counter |
|------|-----------------|---------|
| Availability | First SERP page becomes “the literature” | 4–8 query variants + outlier pack (`query_expander.py --pack contrarian`) |
| Confirmation | Only queries that assume H_lead | Write the falsifying query *before* the confirming one |
| Source selection | English, Northern, convenient PDFs | Geo pack + official-language primaries |
| Recency illusion | Newest thread = new truth | Recency *and* foundational scoring |
| Authority halo | Famous lab / .edu / “professor” | Score methods, not letterhead |

## Interpretation

| Bias | How it shows up | Counter |
|------|-----------------|---------|
| Narrative fallacy | Smooth story over mixed data | Keep contested clusters in Layer 2, not buried |
| False equivalence | 50/50 on a 9-to-1 evidence base | Report evidential weight, not seat count |
| False uniqueness | “No one has studied this” after one search | Coverage analyzer empty-question ≠ empty field |
| Motte-and-bailey | Strong claim in exec, weak claim in appendix | Skeptic persona reads exec last |
| Statistical rhubarb | Percent of percent, missing base rates | Extract raw N, window, denominator |
| Causal inflation | “Linked to” → “causes” in the memo | Linguistic audit: only causal verbs with identification |

## Process

| Bias | How it shows up | Counter |
|------|-----------------|---------|
| Sunk-search | Continuing after two low-yield rounds | Early-stopping rule in the plan |
| Anchoring | First high-integrity source sets the answer | Read a disconfirming anchor second |
| Groupthink (single agent) | One persona, one pass | Analyst → expert → skeptic → decision-maker |
| Semantic drift | Question mutates across tool rounds | Re-read reframed query at each phase |
| Overconfidence | Band = high, n = 1 | `confidence_calibrator.py` overconfidence flags |
| Underconfidence theater | Endless caveats, no decision | Decision-maker pass: “what would reverse this?” |

## Framing effects in *your* output

- Loaded verbs in findings (“devastating”, “slams”, “explodes”) — rewrite to magnitudes.
- Orphan percentages (“up 40%”) — always vs what, from which N, over which window.
- Passive agency (“it is believed”) — name the believer.
- Weasel collectives (“experts say”) — name the experts or drop the clause.

## Pre-mortem on conclusions (mandatory medium+)

Assume the top-line finding is later proven wrong. Write the three most likely error classes:

1. Data gap (you never saw the contradictory primary)
2. Source bias (you over-weighted an aligned producer)
3. Framing / operationalization (you measured the wrong thing)

Then name the search that would have caught it. If you cannot name it, confidence is too high.

## After delivery (meta)

1. Did source selection, tool prompts, or synthesis weighting introduce an unacknowledged slant?
2. Which hypothesis was supported, weakened, falsified, or left open?
3. What single additional source would move confidence most?
4. Log 1–3 method improvements for the next run (case-based, not vibes).
