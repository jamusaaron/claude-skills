---
name: deep-research
description: "Run sophisticated deep research on complex, ambiguous, controversial, or high-stakes questions that need multi-source evidence, source criticism, triangulation, bias audits, uncertainty bands, and audit-ready outputs (executive briefing, claim ledger, source appendix). Use when the user asks for deep research, a comprehensive investigation, multi-source synthesis, a fact-check with evidence, a balanced report on a contested topic, an in-depth study, a research report, an executive briefing, policy/legal/scientific/market analysis with provenance, or any question where a search-then-summarize pass would be insufficient. Triggers: deep research, thorough analysis, evidence synthesis, claim ledger, source credibility, steelman both sides, adversarial review, literature-quality brief."
---

# Deep Research

**Tier:** POWERFUL  
**Category:** Engineering (agentic research methodology)  
**Version:** 2.1.2  
**Dependencies:** Python 3 standard library only (scripts). No paid APIs.

This skill is an **operating system for evidential research**. Follow the phases in order. Do not improvise a vibe-based literature review. Deterministic tools in `scripts/` exist so you are not the only scoring function.

## When to use

- The question is multi-hop, contested, high-stakes, or poorly specified.
- The user needs **decision-grade** output with provenance, not a briefing of the first ten links.
- They ask for audit trails, confidence, steelmanning, or "what would change this".

## When NOT to use

- Single canonical lookup ("what is the capital of X", a well-known constant).
- Pure generation (marketing copy, code, fiction) with no evidential claim.
- Requests for **medical diagnosis, dosing, or legal advice**. You may research *published evidence about a topic*; you do not act as clinician or solicitor. See `references/domain-lenses.md`.
- Requests whose purpose is harm, weapons, or criminal activity — refuse.
- The user already has a complete primary corpus and only wants formatting — use a document skill instead.

If Phase 0 lands on `light` and a single primary will settle it, answer lightly *using this skill's citation rules*, do not run the full DAG as theatre.

## Core principles

1. **Truth-seeking primacy.** Evidence beats narrative convenience, popularity, and the user's preferred conclusion.
2. **Radical transparency.** Claims trace to locators. Methods, assumptions, and holes are written down.
3. **Intellectual humility.** Quantify confidence; steelman rivals; missing evidence is a first-class output.
4. **Balance without false equivalence.** Strongest case on each side, then **relative evidential weight**.
5. **Anti-bias.** Confirmation, availability, selection, framing, motivated reasoning — actively counter them.
6. **User alignment is depth and format**, not the answer.
7. **Auditability.** A stranger can replay plan → queries → scores → ledger → report.
8. **No Grok/Claude lock-in.** Todos, subagents, and social search are optional adapters. Files + Python CLIs are the backbone.

## Load map (progressive disclosure)

| When | Load |
|------|------|
| Before first tool call | `references/tool-orchestration.md` |
| Phase 1 | Run `scripts/research_planner.py`; optionally `assets/research-brief.md` |
| Phase 2 | `references/search-query-playbook.md` + `scripts/search_query_generator.py` |
| Phase 3 | Extraction ACI in tool-orchestration.md |
| Phase 4 | `references/source-evaluation-framework.md` + `scripts/source_scorer.py` |
| Phase 5 | `references/claim-graph-and-triangulation.md` + `scripts/claim_ledger.py` |
| Phase 6 | `references/bias-and-adversarial-analysis.md` + `scripts/bias_audit.py` |
| Phase 7 | `references/uncertainty-and-calibration.md` + `scripts/confidence_calibrator.py` |
| Phase 8 | `references/output-contracts.md` + `scripts/report_assembler.py` |
| Phase 9 | `references/red-team-checklist.md` + `scripts/citation_integrity.py` |
| Phase 10 | `assets/case-log.md` |
| Domain ≠ general | Matching section of `references/domain-lenses.md` only |
| Workers / replan | `references/agentic-research-patterns.md` |
| Scoring the run | `references/quality-bar-and-gaia.md` |

Do not load every reference on every run.

---

## Phase 0 — Intake, risk, tier

Fill `assets/research-brief.md` (internally if the user is terse).

**Risk class**

| Class | Meaning | Default tier |
|-------|---------|--------------|
| R0 | Informational | light or standard |
| R1 | Operational / business decision | standard |
| R2 | High-stakes (legal, medical-adjacent, public, safety) | deep |
| R3 | Adversarial, polarized, misinformation-heavy | adversarial |

**Effort tiers**

| Tier | Sources | Verification | Red-team |
|------|---------|--------------|----------|
| light | 5–10 | optional | starred items only |
| standard | 10–20 | 1 loop on pivotal claims | recommended |
| deep | 20+ | 2 loops | required |
| adversarial | 20+ across ≥3 clusters | 2 loops | required + opposing steelman |

Planner heuristics: `python scripts/research_planner.py --query "..." --json` (add `--tier`, `--domain`, `--jurisdiction` to override).

**Stop if** the request is a when-NOT-to-use case.

---

## Phase 1 — Deconstruct, hypothesize, pre-mortem, DAG

Mandatory before search.

1. Restate the query in **neutral, falsifiable** terms. List implicit assumptions.
2. If high-stakes or ambiguous, write 2–3 interpretations and the scope you will use. Ask the user only when a wrong interpretation would waste the run; otherwise proceed with the stated assumption logged.
3. 3–8 sub-questions; 2–5 falsifiable hypotheses (H1–H5 from the planner are a starting set).
4. Scope: time window, geography, source types, exclusions.
5. Pre-mortem: three ways this research would mislead, and the mitigation (planner emits a stock list — specialize it).
6. DAG: independent nodes marked parallel. Persist the plan (host todo tool **or** `assets/research-plan.md`).
7. Replan triggers and early-stop rules — copy from planner output; do not skip.

Optional domain lens: one pack from `references/domain-lenses.md`. Australian/Commonwealth legal-policy is **opt-in**, never the default personality.

---

## Phase 2 — Horizon scan (query taxonomy)

Generate queries:

```bash
python scripts/search_query_generator.py --topic "..." --domain scientific --json
```

Execute **all families** on standard+: direct, synonym, contradiction, site_academic, site_gov, filetype_pdf, recency, stakeholder, dataset. Contradiction is mandatory even when the user has a preferred answer.

- 3–6 independent searches per round when the host allows parallel tools.
- Snippets are leads. Diversity beats recency-of-index.
- Capture glossary, timeline, stakeholder names, anchor list, outlier list.
- Coverage test: if 70%+ of hits are news explainers, replan toward `site:` and PDFs (`search-query-playbook.md`).

Social/X search: optional adapter; testimony not prevalence.

---

## Phase 3 — Primary-source extraction

For each high-value lead, fetch with an extract-not-interpret instruction (ACI snippet in `tool-orchestration.md`).

Hunt primaries: official statistics, legislation and judgments, filings, registered trials, papers via DOI, datasets. News is a pointer to those.

Maintain `assets/source-ledger.md` / JSON as you go: URL/DOI, title, date, type, provisional band, extracts, cluster id.

If paywalled: open mirror or mark **unverified**. Never fabricate access.

---

## Phase 4 — 12-point source criticism

Score every non-trivial source:

```bash
python scripts/source_scorer.py --title "..." --type government --date 2026-02-01 --url "https://..." --json
```

Bands and allowed uses are defined in `references/source-evaluation-framework.md` and encoded in the script. Do not round a Medium source up to High because it is convenient.

Low-integrity sources stay in the corpus only as **influential narratives**, labelled as such.

---

## Phase 5 — Claim graph, triangulation, conflicts

```bash
python scripts/claim_ledger.py init --path ledger.json --query "..."
python scripts/claim_ledger.py add-claim --path ledger.json --id C1 --statement "..." --type fact
python scripts/claim_ledger.py add-evidence --path ledger.json --id E1 --claim C1 --stance supports --url "https://..." --date 2026-01-15 --band high
python scripts/claim_ledger.py status --path ledger.json
```

Atomize compound sentences. Types: fact / mechanism / interpretation / forecast / value.

Independence = clusters, not URL count. Conflicts: classify factual vs interpretive vs value; **do not average**. Protocol in `claim-graph-and-triangulation.md`.

Pivotal claims (3–5): targeted re-fetch. This is the first verification loop on standard+.

---

## Phase 6 — Steelman and bias audit

For each major camp: strongest evidence-based case, kill-shot facts, residual.

```bash
python scripts/bias_audit.py --input draft.md --domain general
```

The script is a linter. The protocol in `bias-and-adversarial-analysis.md` is the work. Missing perspectives are gaps, not style.

---

## Phase 7 — Uncertainty and calibration

```bash
python scripts/confidence_calibrator.py \
  --claim "..." --n-sources 4 --agreement 0.75 --source-quality 0.7 \
  --recency 0.8 --independent-clusters 2 --has-primary --claim-type fact --json
```

Use conservative inputs (independent count, not raw URLs). Paste **what would change this** onto each pivotal claim. Language must match the band (`uncertainty-and-calibration.md`).

No single percentage for the whole memo.

---

## Phase 8 — Synthesis and decision-grade outputs

Citation-first: ledger → assembler → prose that only glosses existing IDs.

```bash
python scripts/report_assembler.py --ledger ledger.json --findings findings.md --brief brief.md
```

Required layers (compress for light/exec-only, do not drop provenance):

1. Executive briefing  
2. Key findings (claim + locators + band)  
3. Detailed analysis  
4. Claim ledger  
5. Source appendix  
6. Limitations / monitoring  
7. Actionables tied to claim IDs  

Contracts: `references/output-contracts.md`. Templates: `assets/executive-briefing.md`, `assets/full-research-report.md`.

Native citation chips (if the host has them) are **in addition to** C# / URLs, not a replacement.

---

## Phase 9 — Red-team / verifier loop

```bash
python scripts/citation_integrity.py --ledger ledger.json --report report.md --min-sources 2
```

Then `references/red-team-checklist.md` into `assets/red-team-review.md`.

**Hard fail (do not deliver):** hallucinated source; pivotal fact under-sourced; diagnosis/legal-advice voice; forecast sold as fact.

Re-fetch primaries for pivotal claims. Evaluator-optimizer: if a sentence has no locator, delete it or move it to Limitations.

If a replan trigger fires, patch the DAG (`agentic-research-patterns.md`); do not thrash Phase 2.

---

## Phase 10 — Case log

Fill `assets/case-log.md`: what queries produced primaries, what wasted rounds, calibration deltas, 1–3 skill improvements. Next similar query starts by reading the last two logs.

---

## Tool orchestration (summary)

Full adapter map: `references/tool-orchestration.md`.

Always: search, fetch, files, Python CLIs.  
If present: todos, subagents/workers, code execution on tables, social search as testimony, native citations.  
If absent: sequential specialist passes + markdown checklists. **Do not block.**

Worker contract: one sub-question; return ledger-shaped claims/evidence/gaps; no final report.

Early stop when every in-scope sub-question is statused, corroboration rule met, contradiction family run, and the last loop moved confidence <5 points.

---

## Failure modes

| Mode | Symptom | Fix |
|------|---------|-----|
| Plan skip | Immediate search | Restart at Phase 1 |
| SERP capture | News-only corpus | `site:` + PDF families |
| Citation ring | Many URLs, one origin | Cluster; recode n_sources |
| Synthesis drift | Exec summary ≠ restated query | Diff; cut or replan |
| Fluency theatre | Beautiful prose, empty ledger | Stop writing; fill ledger |
| Overconfidence | Very High without primaries | Calibrator caps |
| Sycophancy | Softened findings | Re-steelman |
| Scope theatre | Full DAG on trivia | Phase 0 light / don't use |

---

## Gotchas

- Skipping Phase 1.  
- Treating social as fact.  
- "Three sources" that are one press release.  
- Rounding source bands upward.  
- Writing before citing.  
- False equivalence on unequal evidence.  
- Loading all domain packs.  
- Requiring `todo_write` / X search to exist.  
- Australia-specific defaults on a global query.  
- Diagnosing or advising as counsel.

---

## Scripts (CLI)

All offline-first, `--help` and `--json` (or JSON subcommand output). No network required.

| Script | Role |
|--------|------|
| `scripts/research_planner.py` | Plan, tier, DAG, seed queries |
| `scripts/search_query_generator.py` | Nine-family query set |
| `scripts/source_scorer.py` | 12-point score + band |
| `scripts/claim_ledger.py` | init / add / link / gaps / export |
| `scripts/confidence_calibrator.py` | Conservative band + kill-switches |
| `scripts/bias_audit.py` | Heuristic draft linter |
| `scripts/report_assembler.py` | Contract-shaped draft |
| `scripts/citation_integrity.py` | Corroboration, URLs, orphans, IDs |

Exit codes: `0` ok, `1` quality fail (audit/integrity), `2` usage/IO error.

---

## Assets

`research-brief.md`, `research-plan.md`, `source-ledger.md` + `.json` + schema, `claim-ledger.md` + `.json` + schema, `findings-memo.md`, `executive-briefing.md`, `full-research-report.md`, `red-team-review.md`, `case-log.md`.

---

## Stop conditions (delivery)

Deliver only when quality gates in `output-contracts.md` pass **or** unmet gates are explicitly listed in Limitations with effect on confidence.

Stamp **as of {date}** on contested and fast-moving topics.
