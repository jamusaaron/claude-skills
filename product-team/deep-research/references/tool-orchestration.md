# Tool Orchestration (platform-agnostic)

This skill must run on Claude Code, Codex, Gemini CLI, and similar agents. Do **not** hard-wire a single vendor's citation renderer or social API. Use whatever search/fetch/code tools the host exposes, with the same ACI discipline.

## Decision tree: which local script?

```
Have a raw question?
  → question_decomposer.py
Need a phase plan, search variants, pre-mortem?
  → research_plan_generator.py
Have URLs / metadata to judge?
  → source_credibility.py
Have claims + scored sources?
  → claim_triangulator.py
Need RQ × source coverage?
  → evidence_matrix.py
Need independence / circular citation?
  → citation_graph.py
Notes disagree?
  → contradiction_detector.py
Worried about staleness or missing types?
  → coverage_gap_analyzer.py
Need a deliverable?
  → output_packager.py --kind brief|memo|bibliography|layered
```

All scripts are stdlib, CLI-first, `--help`, `--format json|text`. No paid APIs. No LLM calls.

## Host tools (typical mapping)

| Need | Typical host tool | Rule |
|------|-------------------|------|
| Landscape | web search (parallel queries) | 4–8 variants from the plan; include a disconfirming query |
| Extraction | fetch / browse URL | Ask for verbatim methods, numbers, limitations, funding *before* summary |
| PDFs / tables | fetch + code | Extract tables; do not eyeball a 80-page PDF from a snippet |
| Computation | local Python / code execution | Recompute percentages; never trust a screenshot of a chart |
| Persistence | files in workspace | Keep `notes.json` matching the sample schema |
| Parallel sub-questions | subagents if the host has them | One question per worker; return source ids + quotes, not essays |

If a host has social search, treat hits as testimony (see OSINT reference). If it has a citation component, use it **and** keep the bibliography.

## ACI (agent-computer interface) rules for every tool call

Write instructions as if a careful intern will execute them:

- **Goal:** one extraction job per call
- **Format:** fields you need (quote, page, date, n=)
- **Edges:** "if paywalled, return the error and the DOI; do not paraphrase from memory"
- **Examples:** show a 4-line desired stub
- **Stop:** "do not interpret causal language unless the paper's design section uses it"

Vague "summarize this website" is how numbers get rounded into myths.

## Parallelism

Do in one round when independent:

- Government series + academic review + disconfirming query
- Two sub-questions that do not share a premise

Do **not** parallelize:

- Verification of a claim with its first acquisition
- Synthesis with missing source scores

## Failure recovery

| Failure | Response |
|---------|----------|
| Paywall | DOI, open preprint, official HTML, or disclose gap |
| Dead link | Archive.org / report edition; never invent the quote |
| Empty search | Broader synonym, then specialist `site:`; then declare sparsity |
| Conflicting tables | Prefer the statistical agency vintage; show both |
| Tool error | Narrow the instruction; do not switch to "I recall that…" |

## Optional BYOK (not required)

Users may plug their own bibliographic APIs (Crossref, OpenAlex, official stats APIs). The skill must still complete with browser/search + these scripts. Never require a commercial key.

## Date discipline

Stamp the plan and the deliverable with the host's current date. Rapid topics get a monitoring note, not fake real-time omniscience.

## Related skills (optional, not hard dependencies)

If present in the user's library, they can consume this skill's notes JSON:

- Competitive teardown / competitive intel — market questions
- Product discovery — assumption tests vs literature claims
- UX research — interview evidence vs desk research
- Financial analyst — when the claim is a model, not a citation

Do not block Phase 1 on those skills being installed.
