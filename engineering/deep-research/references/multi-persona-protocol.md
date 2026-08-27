# Multi-persona research protocol

Simulate specialist passes **inside one agent**. This is not a request to spawn unpaid extra models unless the host explicitly has subagents.

## Personas

| Id | When | Job | Failure mode |
|----|------|-----|--------------|
| `analyst` | gather | Extract cards, keep store clean, map questions | Hoards snippets, no claims |
| `domain_expert` | triangulate | Methods, canonical sources, jargon | Credential worship |
| `skeptic` | challenge | Disconfirm, shared provenance, overclaim | Cynicism without alternative |
| `decision_maker` | deliver | So-what, residual risk, reverse-the-call | Demands certainty the evidence cannot give |

Optional fifth for contested politics: `steelman-opponent` writes the best evidential case for the side you like least.

## Sequence

1. Analyst fills the store (no synthesis language).
2. Domain expert re-scores methods and names missing canonical sources.
3. Run scripts: scorer, matrix, contradictions, coverage, calibrator.
4. Skeptic reads *only* the draft findings + contradiction report; must produce at least one material challenge or certify that none survive.
5. Decision-maker rewrites Layer 1 and the decision brief last.

Do not let the analyst write the executive summary on the first pass.

## Host-specific parallelism

If the host can run isolated workers (Claude Code Task tool, Codex/Grok subagents):

- One worker per *independent* sub-question or source pack.
- Each worker writes a summary artifact back into the evidence store — not a finished essay.
- Parent merges with `evidence_store.py merge`.
- Never let workers invent a shared conclusion before merge.

Recipes for Grok-native tools live in `grok-integration-recipes.md`. Claude Code equivalents: TodoWrite for the plan, parallel tool calls for independent searches, Task/subagent only when context isolation is worth it.

## Independence rules

- Workers must not see each other’s synthesis.
- They may see the shared **plan** (questions, exclusions).
- Parent adjudicates contradictions; workers do not vote.

## Done when

Skeptic pass has run, coverage of pivotal questions is adequate or explicitly sparse, and the decision-maker can name the evidence that would reverse the call.
