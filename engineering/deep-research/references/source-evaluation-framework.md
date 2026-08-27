# Source evaluation framework (12-point rubric)

Use with `scripts/source_scorer.py`. Score each non-trivial source. Low-integrity sources stay in the store only as *influential narratives*, never as load-bearing evidence.

## Scoring

Each dimension 0–10. The script applies the weights below and emits a 0–100 score plus band:

| Band | Score | How to use |
|------|-------|------------|
| High | ≥85 | Eligible as pivotal evidence |
| Medium-high | 70–84 | Supporting; pair with one independent high |
| Medium | 55–69 | Context / journalism; chase the primary |
| Medium-low | 40–54 | Cite only with a credibility caveat |
| Low | <40 | Illustrative of a narrative; do not treat as fact |

Weights: methodology 1.3, provenance 1.2, evidential weight 1.2, corroboration 1.1, peer review 1.1, recency 1.0, funding 1.0, counter-evidence 0.9, reproducibility 0.9, framing 0.8, diversity 0.5, integrity (composite) 0.4.

## The 12 points

1. **Provenance & authority** — Who produced this, and what is their track record (retractions, corrections, statutory mandate)? `.gov` / official stats ≠ unbiased, but they are *accountable*.
2. **Recency & relevance** — “Current as of” vs foundational-but-old. A 1998 methods paper can outrank a 2026 listicle.
3. **Methodological transparency** — Sample, controls, power, preregistration, open data. If you cannot say how the number was produced, it is a rumor with typesetting.
4. **Corroboration** — Independent replication, not three outlets rewriting the same press release. Cluster by publisher family.
5. **Funding & conflicts** — Disclosed *and* inferred (industry group, political sponsor, vendor). Keep the source; down-weight it.
6. **Framing & language** — Loaded terms, omitted baselines, false balance, straw men. Cross-check the title against the limitations section.
7. **Evidential weight** — Hierarchy: meta-analysis / primary statute / dataset > well-run observational > news > opinion.
8. **Counter-evidence handling** — Do they steelman the other side or disappear it?
9. **Accessibility & reproducibility** — URL, DOI, archive, data dump. Unverifiable quotes are not evidence.
10. **Peer review & editorial standards** — Journal, official production process, or none. Preprints are first drafts until shown otherwise.
11. **Diversity of perspective** — Unique viewpoint vs echo. Outliers are valuable for coverage, not for weight.
12. **Overall integrity** — One-sentence justification. If you cannot write it, you have not evaluated the source.

## Worked mini-examples

**ABS labour-force release** — provenance 9, methods 8, recency 9, funding 8 → **high**. Caveat: survey error and definition changes.

**Vendor “39.9% productivity” blog** — provenance 5, methods 3, framing 3, recency 7 → **medium-low / low**. Keep as a claim to test, not a finding.

**NBER working paper** — not always peer-reviewed; score peer-review ~4–6 unless later journal version exists; methods may still be excellent.

**X/Twitter thread by a named expert** — testimony. Score social ~2–4 as fact; higher as a pointer to a paper or dataset they cite. Never let virality substitute for corroboration.

## Independence test (mandatory for pivotal claims)

Two URLs are **not** independent if they share:

- publisher family or wire service
- the same dataset, without a new identification strategy
- a PR office as the common origin
- a citation circle that never leaves one lab / think tank

`claim_matrix.py` flags `shared_provenance_risk`. If it fires, you do **not** yet have two sources.

## Recency weighting

- ≤1 year: full credit for “current state” questions
- 1–3 years: still current for most policy/tech
- 3–7 years: keep if foundational or slow-moving (statute, physics)
- >7 years: default stale for “what is true now” unless marked `foundational`

Rapidly evolving legal/tech topics: put **as of [date]** in the executive summary, not a footnote.

## What the script cannot see

The CLI does not fetch pages. If you have quotes, methods notes, COI flags, or `peer_reviewed: true`, put them on the card so scoring is not just URL heuristics. Heuristics are a floor, not a substitute for reading.
