# Quality bar and evaluation thinking

Load this when judging whether a run is done, when red-teaming a draft, or when comparing two research artifacts. Inspired by GAIA-style agent evaluation: **correctness, completeness, and inspectable reasoning** — not fluency.

This skill is not a benchmark harness. Use the questions as a scorecard (0–2 each). A `deep` run should hit ≥18/24. `light` can hit ≥12/24 if scope was honest.

## 1. Completeness (coverage of the asked question)

- Every Phase 1 sub-question has a status in the ledger.
- Out-of-scope items are listed as out-of-scope, not silently omitted.
- Contradiction family was executed (or the case log explains a true null).
- Stakeholder map has more than the user's camp.

Fail: a polished essay that answers a neighbouring question.

## 2. Factual correctness and citation integrity

- Locators resolve (URL well-formed, document exists, quote is in context).
- Numbers include denominator, window, population.
- `citation_integrity.py` error count is 0, or errors are waived in Limitations with a reason.
- No invented papers, DOIs, case names, or "a 2024 Nature study" without a locator.

**Citation laundering fail:** citing a newspaper that cites a blog that cites a tweet as if it were the study.

## 3. Contradiction handling

- Conflicts classified (factual / interpretive / value).
- Relative evidential weight is stated.
- No false tie and no silent drop of the weaker-but-real camp.

GAIA-like agents fail this by picking the first tool result. You will too unless Phase 5 is real.

## 4. Calibration

- Claim-level bands from the calibrator, not a mood.
- Kill-switches are specific.
- Forecasts not sold as facts.

## 5. Process inspectability

A stranger can replay: plan → queries → source scores → ledger → report.

Minimum artifact set for `standard+`:

- research-plan.md (or planner JSON)
- source-ledger
- claim ledger JSON
- report
- red-team-review.md (deep/adversarial)

## 6. Efficiency vs theatre

Scoring **down** for:

- 40 undifferentiated searches that never got fetched
- Subagents that returned essays with no locators
- Repeating Phase 2 after sufficiency was met

Scoring **up** for early stop with disclosed unknowns.

## Quick scorecard

| Dimension | 0 | 1 | 2 |
|-----------|---|---|---|
| Completeness | Missing a core sub-Q | Partial | All in-scope Qs statused |
| Citations | Hallucinated or bare | Partial locators | Replayable locators |
| Contradiction | Ignored | Mentioned | Classified + weighted |
| Calibration | Fake certainty | Bands without drivers | Bands + kill-switches |
| Inspectability | Chat only | Partial files | Full artifact set |
| Efficiency | Thrash | Some waste | Stop rules honored |

## Comparison to "search then summarize"

If the output could have been produced by stuffing the first ten links into a summary, the skill was not used. The delta should be: scored sources, atomized claims, classified conflicts, capped confidence, and an audit trail.

## When this skill loses on purpose

GAIA-style tasks that are a single lookup ("what is the capital of X") should **not** use the full DAG. Phase 0 should return `light` or "do not use this skill". Running deep research on trivia is a quality failure (waste), not a quality success.
