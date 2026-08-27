---
title: "Deep Research"
description: "Deep Research - Claude Code skill from the Engineering - POWERFUL domain."
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

# Deep Research

## Name

Deep Research (POWERFUL) — multi-source evidence pipelines for high-stakes questions.

**Tier**: POWERFUL  
**Category**: Engineering / Knowledge Operations  
**Dependencies**: None (Python standard library only)

## Description

Professional-grade research methodology for agents: not “search then summarize”, but a seven-phase pipeline that deconstructs the question, gathers diverse primaries, scores sources, maps claims to evidence, hunts contradictions, calibrates confidence, and delivers layered, auditable artifacts.

The skill keeps the original deep-research doctrine — truth-seeking, radical transparency, steelman-without-false-equivalence, anti-bias vigilance, agentic replanning — and adds deterministic CLI tools so planning, scoring, coverage, and resume are not left to memory.

**Triggers:** deep research, comprehensive investigation, thorough analysis, multi-source synthesis, fact-check with evidence, balanced report on a controversial topic, in-depth study, research report, executive briefing, policy or legal analysis with an audit trail, continuing / incremental research, “what does the evidence actually say”.

**Do not use** for trivia, single-URL lookups, or tasks that only need a known internal doc.

## Features

- **Seven-phase pipeline:** ingest → plan → gather → triangulate → synthesize → challenge → deliver
- **Falsifiable planning:** questions, hypotheses, scope, pre-mortem, replan triggers, effort tiers
- **Source criticism:** 12-point rubric, recency weighting, shared-provenance detection
- **Claim–evidence matrix** with independence tests and pivotal-claim bars
- **Contradiction classes:** factual vs interpretive vs value-laden
- **Uncertainty ladder** with overconfidence flags
- **Multi-persona passes:** analyst, domain expert, skeptic, decision-maker
- **Resume:** JSON/JSONL evidence store with merge/dedup
- **Query expansion:** boolean, `site:`, `filetype:`, scholarly operators (no paid APIs)
- **Stakeholder outputs:** executive, product, policy/legal, academic, investigative
- **Platform-portable:** Claude Code, Codex, Gemini, OpenClaw; Grok-native recipes optional

## Core principles

1. **Truth-seeking primacy** — evidence and coherence beat narrative, popularity, or vibe.
2. **Radical transparency** — every significant claim has a locator; methods and limits are explicit.
3. **Intellectual humility** — quantify confidence; steelman the other side; say when evidence is absent.
4. **Balance without false equivalence** — strongest evidential case per side, then *weight*, not a 50/50 split.
5. **Anti-bias vigilance** — confirmation, availability, source-selection, framing, semantic drift.
6. **User alignment** — light / medium / deep matched to the actual decision.
7. **Agentic adaptability** — replan when evidence, access, or scope breaks the plan.
8. **Auditability** — a reader can challenge the conclusion from the appendix alone.

Details: `references/research-methodology.md`, `references/cognitive-bias-checklist.md`.

## When to use / decision tree

```
Need a single known fact with a locator?     → skip this skill, just fetch it
Need a ranked shopping list with no stakes? → skip or light effort only
Need a contested / high-stakes / sparse answer?
    Has prior notes or a store?             → resume: coverage_analyzer then gather deltas
    Legal / policy / AU employment?         → mode=legal, geo pack, playbook
    Market / competitor?                    → mode=market, filings pack
    Scientific claim?                       → mode=scientific, reviews first
    Architecture / vendor bench?            → mode=technical, spec + independent bench
    Else                                    → mode=auto, effort=medium default
```

## Mandatory workflow

Never skip ingest/plan or the challenge pass on medium+. Keep a store even on light runs.

### Phase 0 — Ingest

Capture goal, audience, constraints, success criteria, prior store path. Fill `assets/research-brief.md`. If the query is loaded (“prove”, “debunk”, “best”), reframe it in the plan. Flag PII, active litigation, and ToS limits (`references/legal-ethical-boundaries.md`).

### Phase 1 — Plan

Run:

```bash
python scripts/research_planner.py --topic "..." --effort medium --geo GLOBAL --format json -o plan.json
python scripts/query_expander.py --query "..." --geo GLOBAL --after 2024-01-01
```

Persist the plan (Todo list, `plan.json`, or `assets/research-plan.md`) **before** broad search. Include 3–8 questions, 2–5 hypotheses, exclusions, pre-mortem, early-stopping, replan triggers.

### Phase 2 — Gather (horizon then primary)

Execute 4–8 expander queries across packs (gov / academic / news / contrarian), then extract primaries with ACI-style browse prompts (verbatim numbers, methods, limitations, funding, date). Write cards:

```bash
python scripts/evidence_store.py init --output store.jsonl
python scripts/evidence_store.py add --store store.jsonl --title "..." --url "..." --question Q1 --claim "..." --source-type government
```

Social/X is testimony. Paywalls: log failure, find an open primary, do not fabricate access.

### Phase 3 — Triangulate

```bash
python scripts/source_scorer.py --input store.jsonl --format json -o scores.json
python scripts/claim_matrix.py --input store.jsonl --format json -o matrix.json
python scripts/contradiction_detector.py --input store.jsonl --format json -o contra.json
python scripts/coverage_analyzer.py --plan plan.json --store store.jsonl --format json -o coverage.json
python scripts/citation_normalizer.py --input store.jsonl --format json -o biblio.json
```

Pivotal claims need ≥2 independent high/medium-integrity sources **or** one checkable primary. Shared publisher family ≠ independent.

### Phase 4 — Synthesize

```bash
python scripts/synthesis_outliner.py --plan plan.json --matrix matrix.json --coverage coverage.json --audience executive
python scripts/confidence_calibrator.py --input matrix.json --contradictions contra.json
```

Draft into `assets/findings-memo.md` / `assets/decision-memo.md`. Date-stamp the answer.

### Phase 5 — Challenge

Skeptic persona + steelman + pre-mortem on conclusions (`references/multi-persona-protocol.md`). Re-browse the 3–5 pivotal locators. Classify remaining disputes: factual (resolve via primary) / interpretive (present both) / value-laden (map assumptions).

### Phase 6 — Deliver

Layered output (see Quality bar). Optional audit log. Then meta-reflect: 1–3 method improvements.

## Usage

All scripts: stdlib, `argparse`, `--format text|json`, `--help`. Run from `engineering/deep-research/` or with absolute paths.

| Script | Job |
|--------|-----|
| `scripts/research_planner.py` | Decompose topic → questions, hypotheses, scope, DAG |
| `scripts/query_expander.py` | Boolean / site: / filetype: / scholar variants |
| `scripts/evidence_store.py` | `init` `add` `merge` `query` `stats` `export` |
| `scripts/source_scorer.py` | 12-dimension credibility + recency |
| `scripts/claim_matrix.py` | Claim clusters, independence, pivotal gaps |
| `scripts/contradiction_detector.py` | Numeric / negation / antonym clashes |
| `scripts/coverage_analyzer.py` | Empty/thin questions, missing source classes |
| `scripts/citation_normalizer.py` | APA / BibTeX / CSL-JSON-ish, DOI/URL dedupe |
| `scripts/synthesis_outliner.py` | Stakeholder-layered outline |
| `scripts/confidence_calibrator.py` | Uncertainty ladder + overconfidence flags |

```bash
python scripts/research_planner.py --help
python scripts/evidence_store.py --help
```

**Resume:** `coverage_analyzer.py` on the existing store, then `evidence_store.py merge --store current.jsonl --incoming new.json`.

## Examples

### Example 1 — Product decision (medium)

User: “Should we copy Competitor B’s four-day week? Sales says productivity explodes 40%.”

1. Plan in `market`/`technical` hybrid, effort medium.
2. Expander: vendor claims, independent reviews, official trials, disconfirm pack.
3. Store: Iceland official eval (high), Microsoft Japan blog (medium, vendor, 1-month), NBER-style review (high, measurement critique), UK pilot (medium-high, self-report), hype blog (low, narrative-only).
4. Matrix: “≈40% universal gain” is weakly supported / contested; “short trials and self-reports inflate gains” is supported.
5. Decision brief: **trial with pre-registered output metrics**, do not repeat the 40% claim publicly. Reverse-the-call: an independent output-based RCT on comparable SWE teams.

Sample data: `assets/sample_evidence_store.json`, `assets/sample_notes.jsonl`.

### Example 2 — Legal / AU (deep)

User: “Map s351 Fair Work adverse action for a disability/FDV context.”

- `--mode legal --geo AU --effort deep`
- Primaries: Act, FWC decisions, Fair Work ombudsman guidance — not blogs.
- Split black-letter vs practice; note onus, time limits, federal/state.
- This skill **researches**; it does not act as counsel.

### Example 3 — Resume

User: “Continue last week’s climate-policy memo; new IPCC box dropped.”

```bash
python scripts/evidence_store.py merge --store store.jsonl --incoming new_cards.json
python scripts/coverage_analyzer.py --plan plan.json --store store.jsonl
python scripts/source_scorer.py --input store.jsonl --as-of 2026-08-27
```

Only gather the delta; re-run challenge on findings the new primary touches.

### Example 4 — Polarized claim

Steelman the claim from its own sources, score them, present counter-evidence with weight. No moralizing. Date-stamp. If the evidential disparity is large, say so plainly.

### Example 5 — Information-scarce

Coverage report shows empty pivotal questions. Layer 1 leads with sparsity; offer first-principles bounds, analogs (labeled), and an interview/FOI protocol (`assets/interview-protocol.md`).

## Quality bar (definition of done)

A run is not done until:

- [ ] Reframed, falsifiable question and documented scope
- [ ] Evidence store exists (even if small)
- [ ] Every non-obvious high-stakes claim has ≥2 independent high/medium-integrity sources or 1 primary
- [ ] Low-integrity sources, if shown, are labeled illustrative
- [ ] Contested findings appear in Layer 2, not only the appendix
- [ ] Confidence bands with drivers; as-of date on volatile topics
- [ ] Challenge/steelman pass recorded
- [ ] Limitations + specific next queries
- [ ] Locators for web-derived facts (platform citation component if any, **and** bibliography)

Self-score internally (1–5): coverage, traceability, steelman, calibration, bias resistance. Disclose shortfalls.

## Anti-patterns (gotchas)

- Skipping Phase 1 and jumping to search (scope creep + confirmation bias)
- One query strategy; first-page dominance
- Treating social as fact
- “Three articles” that share a press release
- No verification loop on pivotal claims
- Bare URLs without a scored appendix
- Context bloat: landscape only in chat, nothing in the store
- Over-weighting the first good source
- False equivalence or moralizing
- Description-bloat in the live answer — put diary in the log
- Inventing access to paywalled PDFs
- Cross-skill hard wiring — companions are optional

## Tool orchestration (portable)

- **Search:** run expander variants in parallel when independent; diversity over depth on round 1.
- **Fetch:** never browse without an extraction goal; re-fetch for verification.
- **Parallelism:** independent sub-questions and source packs in one turn.
- **Subagents (optional):** one worker per sub-question; merge cards, do not merge essays.
- **Date:** always “as of [today’s date from context]”.
- **ACI:** precise tool instructions, examples, “if empty/paywalled, say so”.

Grok-specific mappings: `references/grok-integration-recipes.md`.

## Edge cases

| Case | Handling |
|------|----------|
| Sparse domain | Lead with sparsity; bounds; interview/FOI |
| Fast-moving | As-of + monitor table |
| Conspiracy / polarized | Steelman then rubric; proportional counter-evidence |
| Legal | Rule vs practice vs guidance; no legal-advice voice |
| Quantitative | Extract N, window, operationalization; no causal verbs without identification |
| Long session | Store + plan files; revisit original intent |
| Sensitive | Minimize PII; trauma-informed precision |
| Non-English | Note translation loss; prefer official translations |

## Effort tiers

| Tier | When | Bar |
|------|------|-----|
| **light** | Time-boxed decision support | Plan + 1–2 search rounds + exec summary + caveats. Store still required. No full persona stack. |
| **medium** (default) | Standard deep research | Full pipeline, verification loop on 3–5 pivotal claims, skeptic pass, appendix. |
| **deep** | Legal, polarized, sparse, or board-level | Multi-persona, continuing store, decision brief, research agenda, audit log. |

Escalate automatically when: the user says “comprehensive” / “audit trail”; the topic is contested; coverage comes back empty on a pivotal question; or the decision is irreversible.

## Script cookbook

```bash
# Light: plan + queries only
python scripts/research_planner.py --topic "$Q" --effort light --format json -o plan.json
python scripts/query_expander.py --query "$Q" --pack government --pack academic --pack contrarian

# Medium: store → score → matrix → coverage → outline
python scripts/evidence_store.py init --output store.jsonl
python scripts/evidence_store.py add --store store.jsonl --title "ABS" --url https://abs.gov.au --question Q1 \
  --source-type government --claim "..." --polarity supports
python scripts/source_scorer.py --input store.jsonl --format json -o scores.json
python scripts/claim_matrix.py --input store.jsonl --format json -o matrix.json
python scripts/coverage_analyzer.py --plan plan.json --store store.jsonl --format json -o coverage.json
python scripts/synthesis_outliner.py --plan plan.json --matrix matrix.json --audience executive -o outline.txt

# Challenge
python scripts/contradiction_detector.py --input store.jsonl --format json -o contra.json
python scripts/confidence_calibrator.py --input matrix.json --contradictions contra.json --format json

# Deliver
python scripts/citation_normalizer.py --input store.jsonl --style apa
python scripts/evidence_store.py stats --store store.jsonl
python scripts/evidence_store.py export --store store.jsonl --output snapshot.json
```

Flags worth knowing:

- Planner: `--mode auto|legal|scientific|market|technical|policy|historical`, `--geo AU|US|UK|EU|GLOBAL`, `--since`, `--exclude`
- Expander: repeatable `--pack`, `--after YYYY-MM-DD`, `--limit`
- Scorer: `--as-of` for recency, `--foundational` for old-but-canonical
- Store: `merge` is the resume primitive; `query --question Q1 --contains "onus"`
- Calibrator: feed the matrix, not raw search snippets
- Outliner: `--audience executive|product|policy|academic|investigative`

Sample fixtures: `assets/sample_evidence_store.json`, `assets/sample_notes.jsonl`, `assets/sample_research_brief.json`. Golden CLI outputs live in `expected_outputs/`.

## Continuing research (resume)

Do not restart from a blank search when a store exists.

1. `coverage_analyzer.py --plan plan.json --store store.jsonl` — what is still empty/thin?
2. Merge new cards only: `evidence_store.py merge --store store.jsonl --incoming delta.json`
3. Re-score with `--as-of` today (recency bands move).
4. Re-run matrix + contradictions on the union, not on the delta alone.
5. Challenge only the findings the new evidence can touch, then rewrite Layer 1.

If the user changes the *decision*, rewrite the brief and questions; do not bolt a new exec summary onto an old question set.

## Interpreting script output

| Artifact | Green | Yellow | Red |
|----------|-------|--------|-----|
| Source scores | Band high / medium-high on load-bearing cards | Medium journalism pointing at a primary | Low blogs used as facts |
| Claim matrix | `supported` + `meets_pivotal_bar` | `weakly-supported` | `contested` on the headline claim with no verification |
| Coverage | Pivotal questions adequate | Imbalanced types | Empty pivotal question |
| Contradictions | None, or interpretive only | Value-laden leftover | High-severity factual pairs |
| Confidence | Band matches source independence | Overconfidence flag | Very-high on n=1 |

Never raise a confidence band by rewriting prose. Raise it by adding an independent primary.

## Persona checklist (copy into the todo list)

- [ ] Analyst: every fetched source is a card with `question_id` and at least one claim
- [ ] Domain expert: methods/funding/limitations extracted for anchors
- [ ] Skeptic: at least one disconfirming query executed; contradiction report read
- [ ] Decision-maker: Layer 1 names the reverse-the-call evidence

Skip a persona only on **light** effort, and say so in limitations.

## Sample fixture expectations

The committed samples are a miniature contested-topic run (four-day week productivity):

- `assets/sample_evidence_store.json` — five cards from high (official trial) to low (hype blog)
- `assets/sample_notes.jsonl` — overlapping claims designed to trigger the contradiction detector
- `expected_outputs/sample_source_scores.json` — official/academic cards outrank the Medium blog
- `expected_outputs/sample_contradictions.json` — factual pairs on the “≈40% universal gain” claim
- `expected_outputs/sample_claim_matrix.json` — headline gain is contested or weakly supported

If you change a scoring heuristic, re-generate those files rather than hand-editing numbers.

Sanity:

```bash
python scripts/source_scorer.py --input assets/sample_evidence_store.json --format json | python -c "import sys,json; d=json.load(sys.stdin); assert d['summary']['low']>=1"
python scripts/contradiction_detector.py --input assets/sample_notes.jsonl --format json | python -c "import sys,json; d=json.load(sys.stdin); assert d['pairs_flagged']>0"
```

## File map

```
engineering/deep-research/
├── SKILL.md                 # This file — doctrine + pipeline
├── README.md                # Extract-and-run quick start
├── scripts/                 # 10 stdlib CLIs
├── references/              # Methodology, rubric, playbooks, ethics
├── assets/                  # Briefs, memos, sample store
└── expected_outputs/        # Golden JSON from the sample fixtures
```

Load `SKILL.md` first. Load a single reference when a phase needs depth. Do not bulk-load the folder.

## Scripts vs judgment

Scripts never call LLMs and never fetch the web. They structure *your* notes. Garbage cards in → confident-looking garbage out. You still have to read.

## Integration (optional companions, not dependencies)

- Competitive landscape → competitive-intel / competitive-teardown if present
- Codebase facts → codebase-onboarding
- RAG system design (different job) → rag-architect
- Document polish → host docx/pdf skills
- Employment AU deep-dive → dedicated legal skills *if installed*

Do not block if they are absent.

## References

- `references/research-methodology.md`
- `references/source-evaluation-framework.md`
- `references/cognitive-bias-checklist.md`
- `references/note-taking-evidence-cards.md`
- `references/research-playbooks.md`
- `references/legal-ethical-boundaries.md`
- `references/query-design.md`
- `references/output-templates-stakeholders.md`
- `references/multi-persona-protocol.md`
- `references/grok-integration-recipes.md`

## Assets

Brief, plan, evidence log, claim matrix, source tracker, findings memo, decision memo, interview protocol, teardown canvas, plus `assets/sample_evidence_store.json` and `assets/sample_notes.jsonl`.

## Post-research reflection

1. Unacknowledged bias in selection, prompts, or weights?
2. Which hypothesis moved, and why?
3. What single source would move confidence most?
4. Plan / ACI / rubric change for next time?
5. Log 1–3 skill-method improvements (this is how the original skill self-evolved).

This is the gold standard for agent-assisted research: exhaustive enough to be honest, efficient enough to stop, critical without cynicism, confident only where the evidence is.
