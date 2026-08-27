---
name: "deep-research"
description: "Activate for sophisticated deep research on complex, ambiguous, controversial, or high-stakes topics requiring multi-source evidence synthesis, rigorous source credibility assessment, bias detection, balanced multi-perspective analysis, uncertainty quantification, reflective verification loops, and production of fully traceable structured research outputs with executive summaries, detailed findings, limitations, and actionable insights. Triggers include deep research, comprehensive investigation, thorough analysis, multi-source synthesis, fact-check with evidence, balanced report on controversial topic, in-depth study, research report, executive briefing, policy or legal analysis requiring audit trails."
---

# Deep Research

**Tier:** POWERFUL  
**Category:** Research & Analysis  
**Domain:** Evidence Synthesis, Critical Inquiry, Decision Support

---

## When to Use

- User asks for **deep research**, **comprehensive investigation**, or **thorough analysis**
- Topic is **ambiguous, contested, high-stakes, or rapidly evolving**
- Output must be **auditable** with traceable citations and confidence bands
- User needs **executive briefing**, **policy analysis**, or **evidence-backed decision support**
- Simple factual lookup is insufficient — synthesis across sources is required

**Do NOT use for:** quick fact checks with one authoritative source, creative writing without evidence requirements, or tasks better served by domain skills (see Related Skills).

---

## Quick Start

```bash
# 1. Generate structured research plan
python3 scripts/research_plan_generator.py --query "Impact of EU AI Act on SaaS" --depth deep --format text

# 2. Score source credibility (12-point framework)
python3 scripts/source_credibility_scorer.py sources.json --format text

# 3. Map claims to evidence
python3 scripts/claim_evidence_mapper.py claims.json --format text

# 4. Build synthesis outline
python3 scripts/synthesis_outline_builder.py plan.json --format text

# 5. Format citations
python3 scripts/citation_formatter.py bibliography.json --style apa --format text

# 6. Analyze research gaps
python3 scripts/research_gap_analyzer.py coverage.json --format text
```

---

## Decision Tree: Depth & Approach

```
User query arrives
│
├─ Single authoritative answer exists? ──YES──► Quick lookup (not this skill)
│
├─ NO: Decompose query
│   │
│   ├─ Depth needed?
│   │   ├─ Light (decision in hours) ──► 3 sub-questions, 5-10 sources, 1 verification pass
│   │   ├─ Medium (brief/report) ──────► 5 sub-questions, 15-25 sources, 2 verification passes
│   │   └─ Deep (audit-grade) ─────────► 8 sub-questions, 30+ sources, 3+ verification passes
│   │
│   ├─ Topic type?
│   │   ├─ Scientific/medical ──► Load references/domain-playbooks.md § Scientific
│   │   ├─ Legal/regulatory ────► Load references/domain-playbooks.md § Legal
│   │   ├─ Business/market ─────► Load references/domain-playbooks.md § Business
│   │   ├─ Policy/government ───► Load references/domain-playbooks.md § Policy
│   │   └─ Contested/polarized ─► Mandatory steelman + verification loop
│   │
│   └─ Output format?
│       ├─ Executive only ──► Layer 1 only (see Output Layers)
│       ├─ Standard report ───► Layers 1-4
│       └─ Audit-grade ───────► Layers 1-5 + evidence ledger
```

---

## Core Principles

1. **Truth-seeking primacy** — Evidence and logical coherence override narrative convenience
2. **Radical transparency** — Every significant claim traceable to sources; methods and limitations documented
3. **Intellectual humility** — Quantify confidence; steelman opposing views; flag weak evidence
4. **Balance without false equivalence** — Present strongest evidence-based arguments; indicate relative weight
5. **Anti-bias vigilance** — Counter confirmation, availability, selection, and framing bias
6. **Traceability** — Outputs allow independent verification; maintain research logs

→ Full methodology frameworks: `references/methodology-frameworks.md`  
→ Source tier taxonomy: `references/source-tier-taxonomy.md`

---

## Mandatory Research Workflow

Execute all phases in order. Document process in an internal research log. Never skip Phase 1.

### Phase 1: Query Deconstruction & Planning

1. Restate query in precise, falsifiable terms; surface implicit assumptions
2. Decompose into 3–8 core research questions and 2–5 testable hypotheses
3. Define scope: temporal, geographic, disciplinary, source types, exclusions
4. Map required evidence types (quantitative, qualitative, legal, expert consensus)
5. Run pre-mortem: identify 3 likely failure modes and mitigations
6. Draft research plan: tool sequence, parallelization, iteration triggers, stopping criteria
7. Persist plan as structured todos or written artifact before any retrieval

**Tool:** `scripts/research_plan_generator.py`  
**Template:** `assets/research-brief-template.md`

**Validation checkpoint:** Plan includes sub-questions, hypotheses, source strategy, verification targets, and output artifacts before proceeding.

### Phase 2: Broad Horizon Scanning

- Formulate 4–8 varied search queries (synonyms, Boolean, site/filetype restrictions, recency)
- Execute parallel searches across web, academic, government, and primary documents
- Prioritize source diversity per `references/source-tier-taxonomy.md`
- Identify anchor sources (high integrity, recent, transparent methodology) and outlier voices
- Capture statistics, timelines, stakeholder maps, terminology glossaries

**Goal:** 70–80% conceptual coverage in 2–3 retrieval rounds.

→ Tool orchestration patterns: `references/tool-orchestration-guide.md`

### Phase 3: Targeted Deep Acquisition

For each high-value lead:
- Extract verbatim quantitative findings, methodology, limitations, funding disclosures
- Pursue primary sources aggressively (official statistics, legislation, filings, peer-reviewed papers)
- Maintain running source ledger with URL/DOI, date, type, provisional credibility, key claims

**Template:** `assets/evidence-ledger-template.md`

### Phase 4: Source Criticism & Credibility Scoring

Apply the 12-point evaluation framework to every non-trivial source.

**Tool:** `scripts/source_credibility_scorer.py`  
**Reference:** `references/source-evaluation-framework.md`

Score each source: High / Medium-High / Medium / Medium-Low / Low with one-sentence justification. Retain low-integrity sources only when they illustrate influential narratives — always caveat.

### Phase 5: Evidence Synthesis & Verification

- Build evidence matrix mapping sources → research questions/hypotheses
- Apply triangulation; explicitly seek disconfirming evidence
- Classify disagreements: factual / interpretive / value-laden
- **Mandatory verification loop** (medium+ depth): re-check 3–5 pivotal claims against primary sources
- Deploy analytical techniques from `references/synthesis-patterns.md`:
  - Steelman + devil's advocate
  - Pre-mortem on conclusions
  - Uncertainty ladder (Very High >90%, High 70–90%, Medium 50–70%, Low <50%)
  - Bias audit and trajectory reflection

**Tools:** `scripts/claim_evidence_mapper.py`, `scripts/synthesis_outline_builder.py`  
**Template:** `assets/counter-argument-worksheet.md`

### Phase 6: Structured Output & Quality Gates

Produce layered deliverables — never raw search results.

| Layer | Content | Template |
|-------|---------|----------|
| 1 — Executive Summary | 150–300 words: core answer, confidence, top implications | `assets/executive-summary-template.md` |
| 2 — Key Findings | Claim + citation + confidence tag per bullet | — |
| 3 — Detailed Analysis | Thematic sections, tables, timelines | `assets/synthesis-memo-template.md` |
| 4 — Evidence Appendix | Source matrix with credibility and contributions | `assets/source-matrix-template.md` |
| 5 — Limitations & Gaps | Gaps, uncertainties, follow-up agenda | — |
| 6 (optional) — Decision Framework | Scenarios, recommendations, decision tree | — |

**Tool:** `scripts/citation_formatter.py` for bibliography formatting  
**Gap analysis:** `scripts/research_gap_analyzer.py`

---

## Quality Gates (Self-Enforced Before Delivery)

- [ ] Every non-obvious claim has ≥2 independent medium+ integrity sources OR 1 primary source
- [ ] Pivotal claims underwent verification loop cross-check
- [ ] Medium-Low and Low sources carry explicit credibility caveats
- [ ] Opposing evidence and uncertainties are not minimized
- [ ] Full audit trail: inline citations + evidence appendix
- [ ] Confidence tags applied consistently via uncertainty ladder
- [ ] Tone is neutral, precise, authoritative without false certainty
- [ ] Findings qualified with "as of [date]" for evolving topics
- [ ] Self-assessment completed (completeness, traceability, balance, calibration)

---

## Anti-Patterns (Highest-Leverage Gotchas)

| Anti-Pattern | Consequence | Fix |
|--------------|-------------|-----|
| Skipping Phase 1 planning | Scope creep, confirmation bias | Always generate plan first; persist as todos |
| Single-strategy searches | First-page dominance, low diversity | 4–8 varied queries + tier diversity |
| Social media as standalone fact | Unverified claims in synthesis | Treat as testimony; corroborate |
| No verification on pivotal claims | Shared-provenance echo | Targeted re-acquisition + cross-check |
| Citation without credibility caveat | Reader over-trusts weak sources | Score every source; caveat Medium-Low/Low |
| False equivalence on contested topics | Misleading balance | Steelman with evidential weight |
| Context bloat in long sessions | Lost state, drift | Persist artifacts; checkpoint summaries |
| Over-weighting early sources | Availability bias | Bias audit + trajectory reflection |

→ Full anti-pattern catalog: `references/methodology-frameworks.md` § Anti-Patterns

---

## Cross-Skill Integration

This skill is self-contained but composes well with:

| Trigger | Skill | When |
|---------|-------|------|
| Competitor/market research | `competitive-teardown`, `competitive-intel` | Business landscape with structured scoring |
| Content/evidence for marketing | `content-strategy`, `copywriting` | Turning research into publishable content |
| SEO/source discovery | `seo-audit`, `ai-seo` | Discovering authoritative web sources |
| Data-heavy analysis | `financial-analyst`, `senior-data-scientist` | Quantitative validation and modeling |
| Regulatory/compliance | `gdpr-dsgvo-expert`, `fda-consultant-specialist` | Domain-specific regulatory research |
| Document output | `landing-page-generator` | Research-backed landing page copy |
| RAG/knowledge systems | `rag-architect` | Building persistent research knowledge bases |

Document cross-skill handoffs in the research log when invoked.

---

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Information-scarce domain | State sparsity; first-principles bounds; recommend primary research steps |
| Rapidly evolving topic | Lead with "as of [date]"; note volatility; recommend monitoring |
| Conspiracy/misinformation | Steelman → full credibility framework → proportional counter-evidence |
| Legal/regulatory query | Distinguish law vs enforcement vs guidance; note jurisdictional scope |
| Quantitative modeling | Extract data → validate assumptions → sensitivity analysis → limitations |
| Sensitive/personal topics | Trauma-informed framing; strict privacy; evidence-based empowerment |

→ Domain-specific playbooks: `references/domain-playbooks.md`

---

## Post-Research Reflection

After delivery, internally log:

1. Bias introduced in selection, framing, or synthesis?
2. Which hypothesis was strongest/weakest supported?
3. What single evidence piece would most change confidence?
4. How would the plan improve on repetition?
5. 1–3 meta-improvements to this skill's methodology

Rate internally (1–5): completeness, traceability, balance, calibration, bias resistance.

---

## Scripts Reference

| Script | Purpose | Input |
|--------|---------|-------|
| `research_plan_generator.py` | Structured plan with sub-questions, hypotheses, milestones | CLI args or JSON |
| `source_credibility_scorer.py` | 12-point source evaluation with weighted scoring | JSON source metadata |
| `claim_evidence_mapper.py` | Map claims to supporting/contradicting sources | JSON claims + sources |
| `synthesis_outline_builder.py` | Layered output outline from plan + evidence | JSON plan |
| `citation_formatter.py` | APA, MLA, Chicago, Harvard bibliography formatting | JSON bibliography |
| `research_gap_analyzer.py` | Coverage gaps, weak links, follow-up recommendations | JSON coverage matrix |

All scripts support `--help`, `--format json|text`, and `--output FILE`.

---

## Progressive Disclosure

Load these references only when needed (saves context tokens):

| Reference | Load When |
|-----------|-----------|
| `source-evaluation-framework.md` | Phase 4 — scoring sources |
| `methodology-frameworks.md` | Phase 1/5 — CRAAP, Feynman, lateral reading |
| `source-tier-taxonomy.md` | Phase 2 — prioritizing source types |
| `synthesis-patterns.md` | Phase 5 — triangulation, steelman, uncertainty |
| `tool-orchestration-guide.md` | Phase 2/3 — search and extraction patterns |
| `domain-playbooks.md` | Edge cases — legal, scientific, business, policy |
