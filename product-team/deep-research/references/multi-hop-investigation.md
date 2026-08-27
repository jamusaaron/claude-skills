# Multi-Hop Investigation Patterns

Deep research is often a **graph walk**, not a keyword. A single hop is "search → first PDF." Multi-hop is "claim → measurement → dataset → funding → contrary specification."

## Pattern 1 — Claim → construct → instrument

1. Someone claims "X improved productivity."
2. Hop: what construct is "productivity"?
3. Hop: what instrument measured it (DORA, revenue/FTE, self-report)?
4. Hop: is the instrument validated for this population?
5. Stop when the construct is explicit or you can label the claim non-comparable.

## Pattern 2 — Result → identification → assumption

1. Paper reports a causal effect.
2. Hop: design (RCT, DiD, RDD, IV, event study, OLS).
3. Hop: parallel trends / exclusion restriction / compliance.
4. Hop: robustness table and failed specs.
5. If assumptions are untestable and unstated, cap confidence at Medium.

## Pattern 3 — Number → table → vintage → revision

1. Statistic appears in a speech or news story.
2. Hop to the table id in the statistical agency.
3. Hop to the revisions policy (preliminary vs final).
4. Hop to the microdata caveats (coverage of informal sector, seasonal adjustment).
5. Cite the table, not the speech.

## Pattern 4 — Institution → incentive → missing data

1. A trade body publishes a "consensus."
2. Hop to members and funders.
3. Hop to the data they uniquely hold and do not release.
4. Search for the regulator or union series that should exist if the claim were symmetric.
5. Absence of the obvious contrary series is itself a finding (disclose it).

## Pattern 5 — Citation chain → lineage collapse

1. Five papers agree.
2. Hop through `cites` edges (`scripts/citation_graph.py`).
3. If they share a hub node, collapse to one lineage.
4. Seek a second hub (different country, different registry, different lab).

## Pattern 6 — Outlier → steelman → fail condition

1. A contrarian result survives headline filters.
2. Steelman its methods.
3. List the empirical result that would kill it.
4. Look for that result. If it exists, the outlier is bounded. If not, report it as unresolved, not as crankery-by-default.

## Pattern 7 — Legal/policy hop

1. Commentary says "the law requires X."
2. Hop to the operative section.
3. Hop to the definition section and any carve-outs.
4. Hop to controlling interpretation (regulator guidance vs binding holding).
5. Hop to enforcement practice (what actually happens).
6. Never stop at a law firm's blog.

## Pattern 8 — Entity resolution

Names collide (Cambridge Analytica vs Cambridge University; NIH vs NIHR). Maintain an entity alias list in notes. Wrong entity is a silent hop error.

## DAG thinking (without extra agents)

Independent hops can be gathered in one round (different sub-questions, different source types). Dependent hops cannot: do not "verify" a claim in parallel with first acquiring its primary table.

Document the hop chain in the evidence log (`assets/evidence-log-template.md`) so a reviewer can replay it.

## Failure modes unique to multi-hop

- **Garden of forking paths:** each hop slightly retargets the question until you have a different project.
- **Rabbit hole of credentials:** infinite author biography, zero methods.
- **Paywall cliff:** hop 3 is the table, hop 3 is blocked — disclose and bound; do not "remember" the number from a secondary.

Max hops before a checkpoint: if you cannot state how the current hop serves a Phase 1 question, stop.
