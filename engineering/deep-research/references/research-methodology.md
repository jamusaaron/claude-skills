# Research methodology

Use this when Phase 1–3 of the deep-research workflow needs more than the SKILL.md summary.

## What counts as evidence

| Class | Examples | Typical role |
|-------|----------|----------------|
| **Primary** | Statute, judgment, dataset, source code, filing, lab protocol, contemporaneous letter | Highest weight when authentic |
| **High secondary** | Systematic review, official statistics bulletin, replicated observational study | Synthesis with methods |
| **Secondary journalism** | Reuters / AP / FT investigations | Pointers to primaries; not the last word |
| **Advocacy / vendor** | NGO briefs, vendor white papers, founder threads | Hypothesis generators; never standalone |
| **Testimony** | Interviews, social posts, eyewitness | Qualitative; must be corroborated for factual claims |

**Triangulation rule:** a finding is *decision-grade* only when at least two of {quantitative, qualitative, documentary} converge, *or* one primary source is independently checkable.

## Research designs you will actually meet

1. **Experiment / RCT** — strongest for causal claims; still check generalizability, attrition, and outcome switching.
2. **Quasi-experiment** — difference-in-differences, RDD, IV. Name the identification assumption; search for placebo tests.
3. **Observational / correlational** — default in market and workplace research. Do not upgrade to causal language.
4. **Qualitative / ethnographic** — high value for mechanism and lived experience; pair with base rates.
5. **Legal-doctrinal** — text of the rule vs. how tribunals apply it. Always split those two.
6. **Historical / archival** — provenance of the document matters as much as its content.
7. **Technical / artifact** — read the spec *and* the implementation; postmortems beat marketing benches.

## Horizon scan then laser

- Round 1: 4–8 query variants (see `query-design.md`) to map the landscape. Stop when new queries mostly echo known frames.
- Round 2: extract from **anchor sources** (method-transparent, recent or foundational, cited by opponents as well as allies).
- Round 3: **disconfirming hunt** — failed replications, minority reports, regulator dissenting statements, “we find no evidence”.
- Round 4: verification loop on 3–5 pivotal claims only.

Goal of scanning is 70–80% *conceptual* coverage, not infinite tabs.

## Operationalizing the question

A topic is not a question. Convert:

- “Is X good?” → “On which metrics, for whom, over what window, vs what baseline, with what harms?”
- “Best tool for Y” → “Which option wins on {latency, cost, lock-in, ops burden} given constraint Z?”
- “Should we do W?” → split into empirical claims and value claims; only the former go in the claim matrix.

Write 3–8 questions that could be *wrong*. If a question cannot be falsified even in principle, it belongs in the values section, not findings.

## Hypotheses

Prefer 2–5:

- **H_lead** — the popular claim survives independent sources.
- **H_alt** — a different mechanism explains the same observations.
- **H_null** — measurement / selection / narrative without causal support.
- **H_scope** — effect exists but only in a narrower slice than advertised.
- **H_incentive** — the evidence base is distorted by who pays and who publishes.

Search for the observation that would *hurt H_lead most*, not the one that would decorate it.

## Continuing / incremental research

1. Keep an evidence store (`scripts/evidence_store.py`) across sessions.
2. On resume: run `coverage_analyzer.py` before new searches.
3. Merge new cards; never silently overwrite quotes or credibility notes.
4. Re-score recency with `--as-of` today’s date.
5. Record replan events in the audit log (what changed the DAG).

## When data is scarce

State sparsity in the executive summary — not the appendix. Bound the claim with:

- first-principles / mechanical constraints
- historical analogs (labeled as analogs)
- what a decisive primary would look like (FOI target, dataset, experiment)

Do not fill silence with fluent prose.

## Australian / jurisdictional work (example, not default)

If the user is in a specific jurisdiction, lock it in Phase 1:

- **AU:** ABS, Fair Work Commission, AustLII, Productivity Commission, ASIC, state vs federal.
- Always distinguish **black-letter** from **enforcement practice**.
- Cross-check explanatory memoranda and Full Bench / appellate treatment.

See `research-playbooks.md` for legal, market, technical, and academic packs.
