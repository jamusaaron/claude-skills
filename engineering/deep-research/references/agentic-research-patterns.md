# Agentic research patterns

Load this when the query is multi-hop, when you will spawn workers, or when a replan trigger fires. These are **operating checklists**, not citations of papers. Names (DRA, Agentic RAG, evaluator-optimizer) are shorthands for behaviours you must actually perform.

## Pattern 1 — Hybrid retrieval

Retrieve across four channels; do not stop at web snippets.

| Channel | Examples | Typical integrity prior |
|---------|----------|-------------------------|
| Web / news | Search + fetch | Medium until scored |
| Documents | User uploads, PDFs, legislation | Score as primary if they are |
| Structured | Ledgers, CSV, APIs, official tables | High if methods exist |
| Testimony | Interviews, social primaries, hearings | Low as prevalence; Medium as "this actor said X on date D" |

**Agentic RAG rule:** every retrieved chunk that will support a `fact` is copied into the evidence ledger with a locator. Generation without that copy is citation theatre.

## Pattern 2 — Orchestrator / workers

One coordinator owns the plan, ledger, and synthesis. Workers own *one* sub-question, lens, or source family.

Worker contract (paste into the worker prompt):

```
Goal: {subquestion}
Do: search + fetch + extract; score sources; return claims in ledger schema.
Do not: write the final report; expand scope; moralize.
Return: claims[], evidence[], gaps[], recommended_next_queries[]
```

Parallelize only DAG-independent nodes (Phase 2 families; Phase 3 fetches of different URLs; two lenses on the same corpus). Merge by **claim id**, not by concatenating essays.

If the platform has no subagents, simulate sequential passes with the same contract and still merge into one ledger.

## Pattern 3 — Dynamic replanning

Do not restart from zero. Patch the DAG.

Triggers (also in `research_planner.py` output):

- Pivotal claim still under-sourced after first acquisition
- >3 unclassified conflicts
- Horizon scan <40% non-news
- New primary kills H1
- Tool/paywall failure on an anchor
- Semantic drift vs Phase 1 restatement

On trigger: write *what changed*, *which nodes re-run*, *what is frozen*. Frozen nodes are a feature (prevents thrash).

## Pattern 4 — Verifier / self-critique loop

Separate **generation** from **checking**. After a draft:

1. Select 3–5 pivotal claims.
2. Re-fetch the primary locators (do not trust your earlier paraphrase).
3. Run `citation_integrity.py` and `bias_audit.py`.
4. Run the red-team checklist.
5. Record deltas: what confidence moved, and why.

Evaluator-optimizer: if the verifier cannot cite a locator, the sentence is deleted or moved to Limitations — not rephrased to sound safer.

## Pattern 5 — Citation-first writing

Order of operations:

1. Ledger complete enough for the tier
2. Assembler
3. Prose that only glosses existing C# / E# / S#
4. Native citations if the platform has them

Writing first and citing later is how hallucinated sources appear.

## Pattern 6 — Evidence sufficiency and early stop

Stop when **all** of these hold:

- Every in-scope sub-question has a status
- Pivotal corroboration rule met
- Contradiction family executed once
- Last verification moved confidence <5 points

Do not stop because the narrative is fluent. Do not continue because the topic is interesting (diminishing returns). Remaining unknowns go to Limitations with a cheapest next observation.

## Pattern 7 — Case-based self-evolution

After delivery, fill `assets/case-log.md`. Next run of a similar query: load the last two case logs and reuse queries/venues that actually produced primaries. This is non-parametric memory, not a license to skip Phase 1.

## Pattern 8 — ACI (agent-computer interface) for tools

Every fetch/search instruction should include:

- Desired extract fields (numbers, methods, funding, limitations, date)
- Output shape (bullet list, table)
- Edge cases ("if paywalled, return the exact error and an open alternative")
- Boundary ("do not interpret; extract")

Vague "summarize this page" is how numbers get rounded and caveats die.

## Platform adapters (optional)

| Capability | Claude Code / Cursor | Codex / CLI | Gemini | Grok-class (optional) |
|------------|----------------------|-------------|--------|------------------------|
| Plan persistence | todos / task list | ISSUE notes / files | plan in doc | `todo_write` if present |
| Parallel search | multiple tool calls | same | same | same |
| Fetch | web fetch / browse | same | same | `browse_page` |
| Workers | Task / subagent | separate sessions | same | `spawn_subagent` |
| Social | skip if absent | skip | skip | `x_semantic_search` as testimony only |
| Citations | whatever the product ships | markdown locators | same | native chips **plus** C# |

**Do not block** if a Grok-only or Claude-only tool is missing. Files plus the Python CLIs are the portable backbone.
