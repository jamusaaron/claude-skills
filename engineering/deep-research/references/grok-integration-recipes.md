# Grok / X-native integration recipes

The original deep-research skill was tuned for Grok (todo_write, spawn_subagent, render_inline_citation, X search). This library skill is **platform-agnostic**. Use this file only when those tools exist. On Claude Code, map as follows:

| Grok-oriented instruction | Portable equivalent |
|---------------------------|---------------------|
| `todo_write` after Phase 1 | Persist the plan (TodoWrite, ISSUE, or `research_planner.py -o plan.json`) |
| `spawn_subagent` researcher | Isolated worker per sub-question if the host has subagents; else serial persona passes |
| `render_inline_citation` | Platform citation component **plus** bibliography from `citation_normalizer.py` |
| `x_keyword_search` / `x_semantic_search` | Public social search if available; else skip and note the gap |
| `browse_page` | Web fetch / browse with ACI extraction prompts |
| `web_search` | Host web search; run expander queries, do not one-shot |

## If you are on Grok

1. After drafting the plan, persist todos: topic, sub-questions, hypotheses, source strategy, verification targets, output artifacts.
2. For independent sub-questions, spawn general-purpose researcher workers with a focused prompt and a summary file. Merge summaries into the evidence store.
3. Every web- or X-derived factual sentence in the user-visible output should use the platform citation component immediately after the sentence.
4. X is **testimony and discovery**, not a fact database. `min_faves` / `since:` help signal; they do not corroborate.
5. Compaction: write the store and plan to files; do not keep the landscape only in chat.

## ACI reminders (any platform)

Tool prompts must be precise, example-rich, edge-case aware (“if paywalled, say so”), and mistake-proofed. Vague “find stuff about X” is how semantic drift starts.

## Best-of-n on contested claims

Spawn or simulate two workers with opposite priors on the same pivotal claim. Parent compares evidence cards, not eloquence. Shared provenance = one source.

## What not to port

Do not require Grok-only components in this skill’s quality gate. A Claude Code or Codex run is complete without `render_inline_citation` if locators exist in the appendix.
