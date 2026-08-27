# Bias and adversarial analysis

Load this in **Phase 6** and again in **Phase 9**. Pair with `scripts/bias_audit.py` (heuristic tripwire) and this protocol (actual thinking).

The audit script will miss sophisticated bias. You still run the steelman on paper.

## Failure modes this phase exists to catch

| Bias | Typical research symptom | Counter |
|------|--------------------------|---------|
| Confirmation | Search queries only paraphrase the user's preferred answer | Mandatory contradiction family (Phase 2) |
| Availability | First High source becomes the thesis | Pre-mortem on conclusions; score later primaries with equal weight |
| Selection | Corpus is English news + one think tank | Stakeholder + gov + academic families; optional jurisdiction pack |
| Framing | Query verbs smuggle the conclusion ("how badly did X fail") | Restate in Phase 1 in falsifiable, neutral terms |
| Motivated reasoning | You need the answer for a decision you already like | Write the strongest case against the decision you expect |
| False equivalence | Two claims of unequal evidential weight presented as a tie | Report relative weight; do not "both-sides" a measurement |
| Sycophancy | Softening findings to match user affect | User alignment is *depth and format*, not conclusion |

## Steelman protocol (mandatory for contested or R2/R3)

For each major position P:

1. **State P as its best advocates would**, using their definitions and their strongest citations. No scare quotes, no "so-called".
2. **List the facts P needs.** If those facts fail, P fails — that is the honest kill-shot.
3. **Run the kill-shot.** If you cannot kill P on evidence, P survives into the report, even if you dislike it.
4. **State the residual.** What would a reasonable P-advocate still believe after your best critique?
5. **Do the same for not-P.** Skipping the user's favoured side is also bias.

Time-box: in `standard` tier, steelman the top two camps. In `adversarial`, steelman three (including a methods-sceptic camp that attacks *everyone's* data).

## Devil's advocate pass (internal critic)

Ask, in writing in the research log:

- Which search did I not run because I expected noise?
- Which primary did I skim because it was long and inconvenient?
- Did I treat lived testimony as nothing, or as everything? (It is evidence of experience, not of prevalence.)
- Did I use "complex" as a way to avoid a signed conclusion where the facts are actually one-sided?

## Loaded language

Replace:

| Avoid | Prefer |
|-------|--------|
| "alarming surge" | "rate rose from A to B in window W, population P" |
| "experts agree" | "Body N, date D, dissent noted / not noted" |
| "debunked" | "claim C1 is inconsistent with sources S# for reasons…" |
| "nothingburger" | "effect size includes zero at 95% CI" / "no public dataset" |
| "proves" | "is consistent with" / "identifies" if the design supports it |

`bias_audit.py` flags a static list. Add domain-specific slurs and applause lights yourself.

## Missing perspectives

Minimum stakeholder set by lens (see also `domain-lenses.md`):

- **Scientific:** original team, independent replicators, methods critics, funders.
- **Legal / policy:** each party, the forum/regulator, implementers, affected cohort.
- **Market:** incumbent, challenger, buyers, regulators, ex-employees (as testimony).
- **Medical (non-diagnostic):** patients, clinicians, regulators, manufacturers, Cochrane-style reviewers.
- **Geopolitical:** official text, local-language reporting, opposition, IOs, conflict datasets.

If a row is empty, that is a **gap**, not a stylistic choice.

## Motivated-reasoning checklist

Score 0–2 each (0 = failed, 2 = clearly handled). Need ≥10/12 before calling Phase 6 done on deep/adversarial tiers.

1. Contradiction queries actually executed (not merely planned).
2. At least one High/Medium-High source against the emerging thesis, or an explicit "none found after these queries: …".
3. Funding disclosed for the three heaviest sources.
4. Definitions frozen before looking at effect sizes.
5. No relative risk without a baseline.
6. Forecasts labelled as forecasts.

## Adversarial topics (R3)

Additional rules:

- Steelman using the *claimant's own* documents before importing mainstream rebuttals (otherwise you attack a straw man).
- Then apply the 12-point rubric to those documents. Many fail provenance and methodology; say so with scores.
- Do not moralize. Evidential disparity is the result.
- Watch for **firehose** tactics: 50 weak claims. Atomize; score; do not chase every branch. Early-stop on branches with no primary.

## What the script cannot do

`bias_audit.py` is a linter. It will:

- Catch "obviously", missing URL-like citations, one host dominating links.
- Miss a politely written one-sided literature review.
- Mis-flag "never" in "never events" or legal "always" in statutory text.

Override false positives in the research log; do not delete the tools.
