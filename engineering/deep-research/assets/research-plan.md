# Research plan

Paste `research_planner.py --format json` output here, or fill manually.

## Reframed query


## Questions

| ID | Priority | Question | Evidence types |
|----|----------|----------|----------------|
| Q1 | pivotal | | |
| Q2 | pivotal | | |
| Q3 | | | |

## Hypotheses

| ID | Statement | Falsification test | Status |
|----|-----------|--------------------|--------|
| H1 | | | untested |

## Scope

- Temporal:
- Geographic:
- Exclusions:

## Pre-mortem (top 3 failure modes)

1.
2.
3.

## Tool DAG / parallelization

- Round A (horizon):
- Round B (primaries):
- Round C (disconfirm):
- Verification loop targets:

## Replan triggers

-

## Personas and passes

- analyst:
- domain_expert:
- skeptic:
- decision_maker:

## Scripts for this run

```bash
python scripts/research_planner.py --topic "..." --format json -o plan.json
python scripts/query_expander.py --query "..." --geo GLOBAL
python scripts/evidence_store.py init --output store.jsonl
```

## Early stopping
