# Uncertainty Calibration

Overconfidence is the cardinal sin of desk research. Calibrate **before** you write Layer 1.

## Confidence bands

| Band | Numeric | When you may use it |
|------|---------|---------------------|
| Very High | >90% | Multiple independent High primaries, stable construct, no serious contrary High source |
| High | 70–90% | Independent lineages agree; remaining uncertainty is magnitude not direction |
| Medium | 50–70% | Directional lean with design or coverage holes |
| Low | <50% | Sparse, single-lineage, or contested factual core |

These are **not** frequentist p-values. They are a communication contract: if you say High and a competent reviewer finds a High contrary primary you never opened, you mis-calibrated.

## Drivers (use in the finding footnote)

List the actual drivers, not vibes:

- Data volume and coverage of the decision population
- Methodological consensus vs one clever paper
- Independence of lineages
- Result of the verification loop (did the quote survive re-extraction?)
- Recency / revision risk
- Construct validity (are we measuring the thing in the user's question?)

## Promotion / demotion rules

- **Cannot** promote a claim to High because the prose is smooth.
- **Must** demote one band if the citation graph shows a single hub.
- **Must** demote if the coverage tool reports `gap` on the question the finding answers.
- **May** promote after a verification loop that recovered the same number from the primary table.
- Preprints: cap at Medium-High unless methods are exceptional *and* replicated.

## Language that matches bands

| Band | Allowed verbs | Forbidden |
|------|---------------|-----------|
| Very High | shows, establishes (for the stated window) | "settled," "beyond doubt" |
| High | indicates, is supported by | "proves," "debunks" |
| Medium | suggests, is consistent with | "we now know" |
| Low | is possible, remains open | "likely" without a base rate |

## Sensitivity

For quantitative claims, state what would flip the sign: different window, different occupation slice, including unpublished nulls. If a reasonable alternate spec flips the sign, you are at Medium or below.

## Self-score (internal, optional in appendix)

Rate 1–5: coverage completeness, traceability, steelmanning, calibration, bias resistance. If calibration ≤2, rewrite Layer 1 to be more humble than Layer 3 feels.
