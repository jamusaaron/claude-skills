# Research Methodology — Plan → Gather → Evaluate → Triangulate → Synthesize → Package

Use this file as the operating system for a deep-research engagement. SKILL.md is the control plane; this reference is the playbook.

## When this methodology applies

Use the full six-phase loop when the question is **ambiguous, contested, high-stakes, or multi-hop** (the answer is not on the first search page). Do not use it for:

- Lookups of a single known fact (one primary source is enough)
- Pure brainstorming with no evidential claim
- Tasks that are really competitive teardown, user-research synthesis, or legal representation — those have dedicated skills. This skill can still supply the evidence spine.

**Effort tiers**

| Tier | When | Min independent sources | Verification |
|------|------|-------------------------|--------------|
| Light | Scoped fact pattern, low stakes | 6 | Top 2 claims |
| Medium | Default for strategy/policy memos | 12 | Top 4 claims |
| Deep | Controversial, legal-adjacent, scientific, or board-level | 20 | Top 5 claims + gap round |

Generate the plan with `scripts/research_plan_generator.py` before any gathering.

## Phase 1 — Query deconstruction and planning (mandatory)

Never search first. First make the question falsifiable.

1. **Restate** the query in terms a primary source could confirm or refute.
2. **Name implicit assumptions** (jurisdiction, population, time window, metric).
3. **Decompose** into 3–8 research questions and 2–5 testable hypotheses.
4. **Bound scope**: temporal, geographic, disciplinary, source types, exclusions.
5. **Map evidence types**: quantitative, qualitative, documentary, legal, experimental, stakeholder.
6. **Pre-mortem**: list the three most likely ways this research will mislead, and the mitigation for each.
7. **Write replan triggers** (contradiction surge, empty primary path, scope-breaking evidence).
8. **Persist the plan** in the session task list / notes file so it survives context compaction.

Run:

```bash
python scripts/question_decomposer.py "QUERY" --format json
python scripts/research_plan_generator.py --query "QUERY" --depth deep --as-of YYYY-MM-DD --format json
```

**Intent clarification rule:** if two interpretations of the query would produce opposite recommendations, stop and surface both interpretations before gathering. Do not silently pick the more interesting one.

## Phase 2 — Horizon scan

Goal: 70–80% of the *conceptual landscape*, not 70% of the answer.

- 4–8 search variants (synonyms, Boolean, `site:`, `filetype:`, recency). The plan generator already emits these.
- Prioritize diversity of *institutions*, not diversity of URLs from the same wire story.
- Tag **anchor sources** (method-transparent, recent or foundational) vs **outlier voices** (contrarian but cited, or influential despite weak evidence).
- Capture: glossary, timeline, stakeholder map, statistic candidates with vintage dates.
- Do **one explicit disconfirming search** even in light tier ("limitations OR replication OR criticism").

Stop this phase when additional queries only reshuffle the same 10 titles.

## Phase 3 — Targeted acquisition

For each high-value lead, extract **before** interpreting:

- Quantitative findings with units, windows, population
- Methods (sample, identification strategy, preregistration)
- Funding and conflicts
- Limitations section (verbatim if short)
- Publication date and version/vintage

Maintain a source ledger using `assets/source-tracker-template.csv` or the JSON schema in `assets/sample-research-notes.json`.

Primary-source bias is a feature: official statistics, statutes, filings, DOIs, datasets. Secondary journalism is a pointer, not a terminus.

## Phase 4 — Source criticism

Score every non-trivial source with the 12-point rubric (`references/source-evaluation-framework.md`) or:

```bash
python scripts/source_credibility.py assets/sample-research-notes.json --as-of YYYY-MM-DD
```

Low-integrity sources stay in the ledger **only** as illustrations of a narrative. They never carry a pivotal claim.

## Phase 5 — Triangulation and synthesis

1. Map sources → questions (`scripts/evidence_matrix.py`).
2. Score claims for independent lineages (`scripts/claim_triangulator.py`).
3. Detect contradictions (`scripts/contradiction_detector.py`).
4. Check recency and missing types (`scripts/coverage_gap_analyzer.py`).
5. Inspect citation graph for circular corroboration (`scripts/citation_graph.py`).

Then apply synthesis moves from `references/synthesis-frameworks.md`:

- Steelman + devil's advocate on every major position
- Classify disputes: factual / interpretive / value-laden
- Uncertainty ladder on each key finding
- Bias audit of *your* search path, not just the sources
- Trajectory check: did the live question drift from Phase 1?

**Verification loop (mandatory at medium+):** pick 3–5 pivotal claims. Re-extract from the primary page. Require a second independent lineage. Document what changed.

## Phase 6 — Package and quality gates

Never dump search snippets. Produce layered output (`scripts/output_packager.py --kind layered`):

1. Executive summary (150–300 words) with confidence
2. Key findings with citations and confidence tags
3. Detailed analysis
4. Annotated bibliography
5. Limitations and follow-up agenda
6. Optional decision/scenario layer

Quality gates are in SKILL.md. If a gate fails, either fix it or disclose the failure in Layer 5. Silent failure is an anti-pattern.

## Adaptive replanning

Replan when:

- A pivotal claim still has one lineage after a targeted search
- Two high-integrity sources disagree on a factual quantity
- The live question has drifted
- Primary access failed (paywall, broken FOI, missing dataset)

Replanning is a *narrowing* operation, not a restart. Keep the restated query stable unless the user changes the decision.

## Session hygiene (long investigations)

- Persist notes as JSON matching `assets/sample-research-notes.json`
- Checkpoint after each phase: questions, sources added, open disputes
- Compress narrative; keep numbers, dates, and source IDs lossless
- Re-read the restated query before writing Layer 1

## Post-research reflection (internal)

1. Unacknowledged selection or framing bias?
2. Which hypothesis survived, which died, which stayed uncertain?
3. What single additional source would move confidence most?
4. One process change for the next similar query

Log these. Do not append them to the user deliverable unless asked.
