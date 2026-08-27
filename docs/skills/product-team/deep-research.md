---
title: "Deep Research"
description: "Deep Research - Claude Code skill from the Product domain."
---

# Deep Research

<div class="page-meta" markdown>
<span class="meta-badge">:material-lightbulb-outline: Product</span>
<span class="meta-badge">:material-identifier: `deep-research`</span>
<span class="meta-badge">:material-github: <a href="https://github.com/alirezarezvani/claude-skills/tree/main/product-team/deep-research/SKILL.md">Source</a></span>
</div>

<div class="install-banner" markdown>
<span class="install-label">Install:</span> <code>claude /plugin install product-skills</code>
</div>


**Tier:** POWERFUL  
**Category:** Product Team  
**Domain:** Research operations, evidence synthesis, source criticism

A desk-research operating system: **plan → gather → evaluate → triangulate → synthesize → package**. Use it when a single search hit would be malpractice.

Local tools are **stdlib Python CLIs** (no ML/LLM APIs, no paid keys). Knowledge bases live in `references/`. Fill-in templates live in `assets/`.

## When to Use

- The question is ambiguous, multi-hop, contested, or decision-grade
- The user wants a brief, memo, literature synthesis, or audit-ready report
- Claims must survive source criticism (credibility, independence, recency)
- You need structured notes that another researcher could continue

**Do not use** for a single known lookup, pure brainstorming, or work that is really a competitive teardown / discovery interview plan / legal representation. Those can *consume* this skill's notes; they are not substitutes for Phase 1.

**Inputs:** a decision question (plus optional constraints: as-of date, geography, depth `light|medium|deep`, excluded source types).  
**Outputs:** plan JSON, scored source ledger, evidence matrix, contradiction report, packaged brief/memo/bibliography/layered report.

## Core Principles

- **Truth over narrative.** Evidence and coherence beat a tidy story.
- **Traceability.** Every non-obvious claim maps to a source id, locator, and integrity band.
- **Humility.** Quantify confidence; steelman the other side; name gaps.
- **Balance without false equivalence.** Weight evidence; do not split the difference with a Low blog.
- **Independence over URL count.** Six reprints of one embargo are one lineage.
- **OSINT-safe.** Public sources and user-supplied files only. See `references/osint-safe-practices.md`.

## Six-Phase Workflow

Never skip Phase 1 or 4. Persist notes in the schema used by `assets/sample-research-notes.json`.

### Phase 1 — Deconstruct and plan

1. Restate the query so a primary source could confirm or refute it. Name population, window, metric, jurisdiction.
2. If two interpretations reverse the recommendation, surface both before searching.
3. Decompose into 3–8 questions and 2–5 hypotheses.
4. Bound scope (time, geography, source types, exclusions).
5. Pre-mortem: three failure modes + mitigations.
6. Write replan triggers and an early-stop rule.
7. Persist the plan (session todos + `assets/research-plan-template.md`).

```bash
python scripts/question_decomposer.py "Does remote-first work increase engineering productivity?" --format json
python scripts/research_plan_generator.py --query "Does remote-first work increase engineering productivity?" --depth deep --as-of 2026-08-27 --geography global --format json
```

Load `references/research-methodology.md` for the full playbook.

### Phase 2 — Horizon scan

Run 4–8 search variants from the plan (synonyms, Boolean, `site:`, `filetype:`, recency). Include **one disconfirming query**. Tag anchor sources vs outlier voices. Stop when new queries only reshuffle the same titles.

### Phase 3 — Targeted acquisition

Extract verbatim: numbers+units, methods, funding, limitations, date/version. Prefer primaries (statutes, tables, filings, DOIs). Log rows in `assets/evidence-log-template.md` and `assets/source-tracker-template.csv`.

Host fetch/browse calls must be ACI-precise: fields wanted, paywall behavior, "do not interpret yet." See `references/tool-orchestration.md`.

### Phase 4 — Credibility scoring

Apply the 12-point rubric (`references/source-evaluation-framework.md`).

```bash
python scripts/source_credibility.py assets/sample-research-notes.json --as-of 2026-08-27
python scripts/source_credibility.py assets/sample-research-notes.json --format json --min-integrity Medium
```

Low-integrity sources stay only as discourse illustrations.

### Phase 5 — Triangulate, contradict, gap-check

```bash
python scripts/evidence_matrix.py assets/sample-research-notes.json
python scripts/claim_triangulator.py assets/sample-research-notes.json --sources assets/sample-research-notes.json
python scripts/citation_graph.py assets/sample-research-notes.json
python scripts/contradiction_detector.py assets/sample-research-notes.json
python scripts/coverage_gap_analyzer.py assets/sample-research-notes.json --as-of 2026-08-27 --freshness-days 730
```

Then: steelman + devil's advocate, dispute classification (factual / interpretive / value-laden), uncertainty ladder, bias audit, trajectory check (did the live question drift?). Details: `references/synthesis-frameworks.md`, `references/bias-fallacy-checks.md`, `references/multi-hop-investigation.md`, `references/uncertainty-calibration.md`.

**Verification loop (medium+):** re-extract 3–5 pivotal claims from the primary locator. Require a second independent lineage. Document stood / revised / dropped.

### Phase 6 — Package

```bash
python scripts/output_packager.py assets/sample-research-notes.json --kind brief --as-of 2026-08-27
python scripts/output_packager.py assets/sample-research-notes.json --kind memo --format json
python scripts/output_packager.py assets/sample-research-notes.json --kind bibliography --format markdown
python scripts/output_packager.py assets/sample-research-notes.json --kind layered --format markdown
```

Template rationale: `references/report-templates-explained.md`. Citation rules: `references/citation-standards.md`.

## Decision Tree — Which Tool

```
Raw question?                         → question_decomposer.py
Need plan + search variants?          → research_plan_generator.py
URLs / metadata to score?             → source_credibility.py
Claims vs scored sources?             → claim_triangulator.py
Question × source coverage?           → evidence_matrix.py
Circular citation / shared org?       → citation_graph.py
Notes disagree?                       → contradiction_detector.py
Stale or missing source types?        → coverage_gap_analyzer.py
Need a deliverable?                   → output_packager.py
Human testimony required?             → assets/interview-protocol-template.md
```

Depth default is **medium**. Use **deep** for board, legal-adjacent, scientific controversy, or anything that will be quoted without you in the room. Use **light** only when the user asked for a bounded scan and stakes are low — still run a disconfirming search.

## Layered Output (default for medium+)

| Layer | Contents |
|-------|----------|
| 1 | Executive summary 150–300 words: answer, confidence, 3–5 implications, one scope sentence |
| 2 | Key findings: claim + source ids + integrity + confidence tag + short rationale |
| 3 | Thematic analysis, tables, timelines |
| 4 | Annotated bibliography |
| 5 | Limitations, uncertainties, follow-up agenda |
| 6 | Optional decision / scenario framework |

JSON and human-readable forms are both first-class (`--format json` vs `text`/`markdown`).

## Quality Gates (block Layer 1 until true or disclosed)

- Pivotal claims: ≥2 independent High/Medium lineages **or** one named primary, after verification
- Medium-Low / Low sources caveated; Low never carries the headline
- Contrary evidence steelmanned, not buried
- Every high-stakes sentence retrievable via source id + locator
- Confidence language matches the band (`references/uncertainty-calibration.md`)
- As-of date on volatile topics
- Bias audit and trajectory check completed internally

## Anti-Patterns (highest leverage)

- Searching before a written plan
- One query strategy / first-page capture
- Treating social posts as prevalence or fact
- "Three sources" that share a dataset or embargo
- Skipping the verification loop on the claims that matter
- Bare URLs with no integrity band
- False equivalence or moralizing on contested topics
- Upgrading Low evidence to High with fluent prose
- Silent paywall failure replaced by "memory"
- Cross-skill blocking (this package is self-contained)

## Worked Mini-Example

Question: *Does remote-first work increase engineering productivity in mid-size SaaS (2020–2026)?*

1. Decomposer tags `causal` + `quantitative`; forces a definition question (throughput vs cycle time vs innovation).
2. Plan (deep) emits disconfirming variants and a pre-mortem on construct switching.
3. Sample notes in `assets/sample-research-notes.json` mix High official stats, a preprint, a vendor survey, and a Low blog.
4. Credibility script bands the blog **Low** and the vendor **Medium-Low**.
5. Triangulator marks seniority-split as `single_lineage`; contradiction detector flags throughput-up vs cycle-time-down as a **factual-metric** dispute.
6. Packager Layer 1 must say the sign **depends on the metric** — not "remote work works."

## Edge Cases

- **Sparse domains:** say so; give mechanism bounds; recommend lawful primary collection (FOI, expert, user data). Do not fake density.
- **Fast-moving topics:** "Status as of [date] is X; Y may shift. Monitor Z."
- **Polarized claims:** steelman from the claim's own sources, then apply the rubric. Let evidential weight speak.
- **Legal/policy:** separate black-letter text, guidance, and enforcement. This skill does not replace counsel.
- **User documents:** cite as user-supplied with filename/hash; never pretend they are public.
- **Non-English:** note translation risk; prefer official translations for operative text.

## Dependencies

- **Python 3.9+ standard library only** (`argparse`, `json`, `csv`, `re`, `datetime`, `urllib.parse`, `collections`).
- No pip packages. No network from scripts. No LLM calls.
- Optional BYOK bibliographic APIs are user-side and never required.

## Package Map

| Path | Role |
|------|------|
| `scripts/question_decomposer.py` | Query type, questions, hypotheses, evidence needs |
| `scripts/research_plan_generator.py` | Phased plan, search variants, pre-mortem |
| `scripts/source_credibility.py` | 12-point integrity bands |
| `scripts/claim_triangulator.py` | Independent-lineage scoring |
| `scripts/evidence_matrix.py` | RQ × source matrix |
| `scripts/citation_graph.py` | Hubs, isolates, shared lineage |
| `scripts/contradiction_detector.py` | Consensus vs disputes |
| `scripts/coverage_gap_analyzer.py` | Recency + coverage gaps |
| `scripts/output_packager.py` | Brief / memo / biblio / layered report |
| `references/` | Methodology, rubric, synthesis, bias, OSINT, citations, multi-hop, templates, orchestration, calibration |
| `assets/` | Templates + `sample-research-notes.json` |

## Related Skills (optional, not required)

- Competitive teardown / competitive intel — when the object is a rival product
- Product discovery — when the object is an untested product assumption
- UX researcher-designer — when the object is user behavior you can interview
- Financial analyst — when the object is a model, not a literature claim
