# Red-team checklist

Load this in **Phase 9** before the user-facing report leaves the building. Print a copy into `assets/red-team-review.md`. Attack the draft; do not admire it.

For `adversarial` and all R2/R3 work this pass is mandatory. For `light`, run the starred items only.

## Identity of the attacker

You are not the synthesizer. You want the draft to *fail* if it can. If you cannot find a problem, you probably did not try.

## Attacks

### 1. Cherry-picking *

List the three strongest omitted sources you already saw in the scan. If any would change a pivotal claim, the draft is incomplete.

### 2. Overconfidence *

For each High / Very High band: re-run `confidence_calibrator.py` with `--independent-clusters` reduced by one. If the band collapses, the original cluster was fake independence.

### 3. Stale data *

Circle every number. Is the date inside the scoped window? For law and prices, yesterday can be stale.

### 4. Citation laundering *

Walk one hop back from each news cite. If the primary is a press release or a tweet, recode.

### 5. Hallucinated sources * (zero tolerance)

Every title, DOI, case citation, and URL must have been fetched or present in the ledger. If you cannot open it in this session, it is unverified — not "probably real".

Invented sources are a **hard fail**. Delete the sentence.

### 6. Quote mining

Re-read the extract in surrounding paragraphs. Limitations sections often negate the headline.

### 7. Definition slide

Did "unemployment", "safety", "revenue", or "AI" change meaning between C1 and C4? Freeze definitions or split claims.

### 8. Base-rate neglect

Relative changes without baselines. "300% increase" from n=1 to n=4.

### 9. Mechanism laundering

A correlation (C1) used as if it were identification (C2). Split.

### 10. Scope / user-intent drift *

Diff the Phase 1 restatement against the executive briefing. If they diverge, rewrite the briefing or replan.

### 11. Sycophancy / moralizing

Any sentence that exists to please or scold rather than to report evidence. Cut.

### 12. False equivalence

Two camps, unequal evidence, written as a tie. Fix the weights.

### 13. Single-cluster corpus

`bias_audit.py` dominant host, or all PDFs from one ministry. Add a second cluster or downgrade.

### 14. Tool-output worship

Snippets, SERP titles, and model-generated "according to the page" paraphrases treated as quotes. Re-extract.

### 15. Actionables that do not follow

Each action maps to a supported claim. If not, move to "speculative options".

## Pass / fail

**Fail (do not deliver):** hallucinated source; pivotal fact with < required independents; medical/legal advice voice; unlabelled forecast as fact.

**Revise:** any non-star item found.

**Pass:** starred items clean; remaining issues listed in Limitations.

## Sign-off block

```
Red-team date:
Tier / risk:
Starred items: pass / fail
Hallucinated sources found: yes / no
Pivotal claims re-fetched: [C# list]
Residual risks:
Reviewer (agent pass id):
```
