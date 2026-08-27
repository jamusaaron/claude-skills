# Tool orchestration (platform-agnostic)

Load this before the first tool call. Details of DRA/worker patterns are in `agentic-research-patterns.md`. This page is the **adapter map** plus ACI snippets.

## Portable backbone (always available)

These do not depend on any one vendor:

1. Files in `assets/` (brief, plan, ledgers, report, case log)
2. Python CLIs in `scripts/` (plan, score, ledger, queries, calibrate, audit, assemble, integrity)
3. Fetch whatever web/browse tool the host exposes
4. A todo list *or* a markdown checklist if todos are missing

## Capability matrix

| Need | Do this | Fallback |
|------|---------|----------|
| Persist plan | Host todo tool | `assets/research-plan.md` |
| Horizon scan | Parallel search calls | Serial searches; still all families |
| Extract primary | Fetch/browse with ACI extract prompt | User-provided PDF |
| Score source | `source_scorer.py` | Manual table using the 12-point rubric |
| Graph claims | `claim_ledger.py` | `assets/claim-ledger.md` |
| Workers | Host subagent / Task tool | Sequential specialist passes, same contract |
| Social testimony | Host X/Reddit tools if any | Skip; do not invent posts |
| Native citations | Host chips / footnote API | Markdown locators + C# |
| Code on tables | Host code execution | Describe the calculation; do not fake precision |

## Optional Grok-class adapters

If and only if these tools exist in the session, they are useful:

- `todo_write` — persist Phase 1; mark phases complete
- `x_keyword_search` / `x_semantic_search` — testimony and leak hunting; corroborate before factual use
- `browse_page` — verbatim extract instructions
- `spawn_subagent` / `task` — workers with the contract in `agentic-research-patterns.md`
- Native citation renderers — use **in addition to** ledger IDs

None of these are required to complete the skill.

## ACI extract prompt (paste)

```
Extract, do not interpret.
Return:
- title, authors/org, date, URL
- funding / COI if stated
- methods in their words (sample, window, controls)
- every quantitative finding with units and denominators
- limitations / caveats section verbatim (trim only boilerplate nav)
- if paywalled, truncated, or JS-blocked: exact failure + any open alternative mentioned
```

## Search batch (paste)

Issue independent queries in one turn when the host allows parallel tools. Example batch: 1 direct, 1 contradiction, 1 `site:.gov`, 1 `filetype:pdf`, 1 recency, 1 stakeholder.

## Compaction survival

Long sessions lose state. Write to disk early:

- `plan.json` from `research_planner.py --json`
- `ledger.json` after every new claim
- source scores JSON beside the ledger

If the host compact/summarizes, **reload those files**, do not trust the summary of your own work.

## Failure recovery

| Failure | Move |
|---------|------|
| Empty SERP | Broaden once, then change family (`site:`, filetype) |
| Paywall | Open repository, official mirror, preprint, or mark unverified |
| Truncated extract | Re-fetch with section-limited instructions |
| Rate limit | Checkpoint ledger; resume with remaining DAG nodes |
| Conflicting tool answers | Prefer fetched primary text over search snippets |
