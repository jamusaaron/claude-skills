# Synthesis Frameworks

Synthesis is where fluent writing most often launders weak evidence. Use these moves in order.

## 1. Evidence matrix before narrative

Rows = research questions. Columns = sources. Cell = polarity + integrity weight.

```bash
python scripts/evidence_matrix.py assets/sample-research-notes.json
```

Do not write Layer 1 until each pivotal question is `covered` (≥2 sources) or explicitly `gap`.

Weighting used by the script: High=3, Medium-High=2.5, Medium=2, Medium-Low=1, Low=0.4; contradicting polarity is negative. Net weight is a **diagnostic**, not a vote. One High primary can beat five Low blogs even if the blogs "win" a naive count.

## 2. Triangulation (convergence across kinds)

Seek agreement across:

- Quantitative vs qualitative vs documentary
- Independent institutions
- Independent identification strategies (not three regressions on one panel)

```bash
python scripts/claim_triangulator.py assets/sample-research-notes.json --sources assets/sample-research-notes.json
```

Verdicts: `corroborated` | `provisionally_corroborated` | `single_lineage` | `contested` | `unverified`.

**Rule:** a claim that is `single_lineage` cannot appear in the executive summary without the lineage named.

## 3. Dispute classification

When sources disagree, classify before you "average" them:

| Type | Test | Treatment in output |
|------|------|---------------------|
| Factual | Same metric, same window, different number | Resolve via primary table / errata / vintage |
| Interpretive | Same facts, different mechanism | Steelman both; report evidential weight |
| Value-laden | Disagreement is about ought, not is | Map values; do not fake an empirical tie |

```bash
python scripts/contradiction_detector.py assets/sample-research-notes.json
```

The detector is heuristic. Always read the paired texts. If overlap is high and polarity flips, it is probably real.

## 4. Steelman + devil's advocate (paired)

For each major position:

1. Write the strongest evidence-based version a competent advocate would accept.
2. Attack *that* version, not a cartoon.
3. Record what survived.

Do this **in the deliverable** for contested topics, not only in internal notes. Readers should see you have occupied the strongest opposing ground.

## 5. Pre-mortem on conclusions

Assume the top-line finding is later shown false. Name:

- The most likely evidential hole
- The search you skipped
- Whether measurement (construct validity) or bias (selection) is the bigger risk

If you cannot name a plausible failure, your confidence is uncalibrated — drop a band.

## 6. Temporal trend, not snapshot-as-eternity

Describe how expert consensus and data vintage moved. A 2020 COVID-era paper and a 2025 panel are not the same claim. Coverage tool:

```bash
python scripts/coverage_gap_analyzer.py assets/sample-research-notes.json --as-of 2026-08-27
```

## 7. Stakeholder power-interest

Who benefits if this finding is believed? Who holds the data? Who cannot speak on the record?

This does not decide truth. It decides **how hard you look for missing contrary evidence**.

## 8. Narrative vs data

When lived experience conflicts with statistics:

- Privilege measurement for prevalence/magnitude claims
- Privilege testimony for mechanism, harm, and "what it's like"
- Explain why the narrative persists (lag, selection, incentives, real subgroup)

Never "debunk people" with an aggregate that excludes them.

## 9. First principles / analogical backup

When empirical density is low: label clearly as **mechanism reasoning** or **historical analog**, give base rates, and refuse to upgrade confidence above Low/Medium.

## 10. Trajectory reflection

Before packaging, re-read the Phase 1 restated query. Check:

- Semantic drift (you answered a sexier neighbor question)
- Early-source overweight (first paper became the frame)
- Premature convergence (stopped at the first tidy story)

If drift happened, either re-scope with the user or rewrite Layer 1 to the original decision.

## Synthesis anti-patterns

- "Studies show" with no count, designs, or independence
- Averaging an RCT with a blog
- False balance ("on the one hand") when evidential weight is 9:1
- Hiding the metric switch (productivity₁ vs productivity₂)
- Executive summaries that omit the main limitation
