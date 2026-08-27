---
title: "Deep Research"
description: "Production-grade agentic research: query deconstruction, hybrid retrieval, 12-point source criticism, claim graphs, calibrated uncertainty, and audit-ready briefings."
---

# Deep Research

<div class="page-meta" markdown>
<span class="meta-badge">:material-rocket-launch: Engineering - POWERFUL</span>
<span class="meta-badge">:material-identifier: `deep-research`</span>
<span class="meta-badge">:material-github: <a href="https://github.com/alirezarezvani/claude-skills/tree/main/engineering/deep-research/SKILL.md">Source</a></span>
</div>

<div class="install-banner" markdown>
<span class="install-label">Install:</span> <code>claude /plugin install engineering-advanced-skills</code>
</div>

**Tier:** POWERFUL  
**Category:** Engineering  
**Tags:** research, evidence synthesis, source criticism, claim graphs, agentic RAG, calibration

## Overview

Deep Research is an operating system for investigations that a search-then-summarize pass cannot carry: contested topics, high-stakes decisions, and multi-hop questions that need provenance. Agents follow an 11-phase DAG (intake through case log), score sources on a 12-point rubric, atomize claims into a ledger, cap confidence conservatively, and ship layered outputs (executive briefing, findings, limitations, actionables, source appendix).

The package is standalone: Python CLIs are standard-library only, offline-first, and emit JSON or human text. Optional platform adapters (todos, subagents, social search, native citation chips) are documented but not required.

## When to use

- Deep research, comprehensive investigation, multi-source synthesis
- Fact-check with evidence; balanced report on a contested topic
- Policy, scientific, market, legal-research, or technical due-diligence briefs that need an audit trail
- Any question where fluency without locators would be a failure

## When not to use

- Single canonical lookups
- Pure generation with no evidential claim
- Medical diagnosis, dosing, or legal advice (published-evidence research only)
- Harmful or criminal purposes

## Workflow (Phases 0–10)

0. Intake / risk class (R0–R3) / effort tier (light, standard, deep, adversarial)
1. Query deconstruction, hypotheses, pre-mortem, DAG plan
2. Horizon scan across nine query families (including contradiction)
3. Primary-source extraction (extract, do not interpret)
4. 12-point source criticism with numeric bands
5. Claim graph, triangulation, conflict classification
6. Steelman + bias audit
7. Uncertainty quantification and calibration caps
8. Synthesis into the output contract
9. Red-team / verifier loop and citation integrity
10. Case log for the next similar run

## Tools

| Script | Role |
|--------|------|
| `research_planner.py` | Structured plan from a query |
| `search_query_generator.py` | Diversified query taxonomy |
| `source_scorer.py` | 12-point integrity score |
| `claim_ledger.py` | Claim–evidence graph |
| `confidence_calibrator.py` | Conservative confidence bands |
| `bias_audit.py` | Heuristic draft linter |
| `report_assembler.py` | Contract-shaped report |
| `citation_integrity.py` | Corroboration and locator checks |

```bash
python engineering/deep-research/scripts/research_planner.py --query "Does retrieval quality dominate agentic RAG accuracy?" --json
python engineering/deep-research/scripts/source_scorer.py --title "Example" --type government --date 2026-02-01
```

## Full skill

See the source package: [engineering/deep-research/SKILL.md](https://github.com/alirezarezvani/claude-skills/tree/main/engineering/deep-research/SKILL.md).
