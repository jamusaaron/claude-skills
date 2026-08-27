# Report Templates Explained

Templates live in `assets/`. This file explains **when to use which** and what "done" looks like. Generate machine-structured versions with `scripts/output_packager.py`.

## Decision tree

```
Need a 1-pager for a decision-maker?     → research brief
Need a working synthesis for a team?     → synthesis memo
Need an audit trail of sources?          → annotated bibliography
Need the full professional artifact?     → layered report (default for deep)
Need to collect human testimony?         → interview protocol
Need to track acquisition in flight?     → source tracker + evidence log
Need to freeze the plan?                 → research brief (scoping) + plan JSON
```

## Research brief (`assets/research-brief-template.md`, `--kind brief`)

**Audience:** executives, PMs, counsel who will not read Layer 3.  
**Length:** 150–400 words + 3–7 bullets.  
**Must include:** bottom line, confidence band, 3 implications, 1-sentence limitation.  
**Must not include:** hunt narrative, tool logs, every caveat known to humanity (those go to Layer 5).

Done when a reader can make the *decision* or know they lack the evidence to make it.

## Synthesis memo (`assets/synthesis-memo-template.md`, `--kind memo`)

**Audience:** working group.  
**Adds:** dispute table, stakeholder map, open questions, what was *not* searched.  
**Done when:** another researcher could continue without a meeting.

## Annotated bibliography (`assets/annotated-bibliography-template.md`, `--kind bibliography`)

**Audience:** auditors, future you, legal hold.  
Each row: citation, type, integrity, contribution, limitations, relevance.  
Low-integrity sources belong here with `illustrative only`.

## Layered report (`--kind layered`)

The default deep-research deliverable. Six layers (see SKILL.md). Keep Layer 1 readable if Layers 3–6 are stripped.

## Interview protocol (`assets/interview-protocol-template.md`)

Use when humans are the evidence (elite interviews, FOIA follow-up calls, user testimony). Not a journalism gotcha script: purpose, consent, recording rules, question map back to research questions, disconfirming prompts.

## Evidence log (`assets/evidence-log-template.md`)

Append-only. One row per extract: source id, locator, quote/number, claim id, hop notes. This is the anti-hallucination file.

## Source tracker (`assets/source-tracker-template.csv`)

Operational spreadsheet analog of `sources[]` in JSON. Use in tools that prefer CSV; convert to JSON before scripts if needed.

## Quality bar shared by all templates

- As-of date in the header
- Confidence language matches `references/uncertainty-calibration.md`
- No pivotal fact without a source id
- Contested topics: steelman visible in the same document
