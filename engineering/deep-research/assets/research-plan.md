# Research plan

Populate from `python scripts/research_planner.py --query "..." --json` then edit.

- **As of:**
- **Query restated:**
- **Domain / jurisdiction pack:**
- **Risk class / effort tier:**
- **Budget (sources, loops, max tool rounds):**

## Sub-questions

1.
2.
3.
4.
5.

## Hypotheses (falsifiable)

| ID | Statement | Falsifier | Status |
|----|-----------|-----------|--------|
| H1 | | | untested |
| H2 | | | untested |
| H3 | | | untested |

## Source types to hunt

-

## Search families (paste generator output)

See `scripts/search_query_generator.py`. Contradiction family is mandatory.

## DAG

| Node | Name | Depends on | Parallel? | Done? |
|------|------|------------|-----------|-------|
| P0 | intake | — | no | |
| P1 | deconstruct | P0 | no | |
| P2 | horizon scan | P1 | yes | |
| P3 | primary extract | P2 | yes | |
| P4 | source criticism | P3 | yes | |
| P5 | claim graph | P4 | no | |
| P6 | steelman / bias | P5 | no | |
| P7 | uncertainty | P5 | no | |
| P8 | synthesis | P6,P7 | no | |
| P9 | red-team | P8 | no | |
| P10 | case log | P9 | no | |

## Pre-mortem (top failure modes)

1.
2.
3.

## Replan triggers

-

## Early-stop rules

-

## References to load this run

-
