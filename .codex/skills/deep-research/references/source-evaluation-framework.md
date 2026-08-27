# Source Evaluation Framework

12-point structured evaluation for every non-trivial source in deep research. Score each criterion 1–5, then compute weighted composite.

**Automate scoring:** `python3 scripts/source_credibility_scorer.py sources.json --format text`

---

## Scoring Scale (All Criteria)

| Score | Label | Meaning |
|-------|-------|---------|
| 5 | Excellent | Gold standard; minimal concerns |
| 4 | Good | Reliable with minor caveats |
| 3 | Adequate | Usable with noted limitations |
| 2 | Weak | Significant concerns; corroborate required |
| 1 | Poor | Unreliable; illustrative only |

---

## The 12 Criteria

### 1. Provenance & Authority (Weight: 10%)

**Evaluate:** Institutional reputation, author credentials, track record of accuracy, history of retractions.

| Score | Indicators |
|-------|-----------|
| 5 | Top-tier institution, recognized domain expert, clean track record |
| 3 | Credible but not leading; author credentials unclear |
| 1 | Anonymous, unknown entity, history of errors/retractions |

**Red flags:** No author attribution, fake journals, impersonation domains.

### 2. Recency & Relevance (Weight: 8%)

**Evaluate:** Temporal fit to research scope; distinguish "current as of" vs outdated but foundational.

| Score | Indicators |
|-------|-----------|
| 5 | Published within scope window; directly addresses query |
| 3 | Slightly dated but still relevant; foundational older work |
| 1 | Clearly outdated for scope; superseded by newer evidence |

### 3. Methodological Transparency (Weight: 10%)

**Evaluate:** Sample size, controls, statistical methods, preregistration, open data/code availability.

| Score | Indicators |
|-------|-----------|
| 5 | Full methods, open data, preregistered, reproducible |
| 3 | Methods described but incomplete; limited reproducibility |
| 1 | No methodology; assertions without supporting data |

### 4. Corroboration (Weight: 10%)

**Evaluate:** Independent replication, convergence with other high-quality sources.

| Score | Indicators |
|-------|-----------|
| 5 | Independently replicated; multiple convergent high-quality sources |
| 3 | Partially corroborated; some independent support |
| 1 | Standalone claim; contradicted by other sources |

**Critical:** Three sources citing the same press release = ONE source for corroboration.

### 5. Funding & Conflicts of Interest (Weight: 8%)

**Evaluate:** Disclosed and undisclosed financial, institutional, or ideological interests.

| Score | Indicators |
|-------|-----------|
| 5 | No conflicts or fully disclosed with mitigation |
| 3 | Potential conflicts disclosed; assess impact |
| 1 | Undisclosed industry funding; obvious advocacy bias |

### 6. Framing & Language (Weight: 7%)

**Evaluate:** Loaded terminology, selective omission, false balance, straw-man treatment.

| Score | Indicators |
|-------|-----------|
| 5 | Neutral, precise language; fair treatment of alternatives |
| 3 | Some framing bias but core data intact |
| 1 | Propagandistic; cherry-picked data; straw-man arguments |

### 7. Evidential Weight (Weight: 10%)

**Evaluate:** Quality and quantity of supporting data vs assertion.

| Score | Indicators |
|-------|-----------|
| 5 | Primary data, large sample, robust analysis |
| 3 | Mix of data and expert opinion |
| 1 | Pure assertion; anecdote presented as evidence |

### 8. Counter-Evidence Handling (Weight: 8%)

**Evaluate:** Does the source engage with contradictory findings?

| Score | Indicators |
|-------|-----------|
| 5 | Acknowledges and addresses counter-evidence rigorously |
| 3 | Mentions but dismisses without engagement |
| 1 | Ignores known contradictory evidence entirely |

### 9. Accessibility & Reproducibility (Weight: 8%)

**Evaluate:** Can claims be independently verified from cited sources?

| Score | Indicators |
|-------|-----------|
| 5 | Full text, data, and citations accessible; verifiable |
| 3 | Partially accessible; some paywall or missing references |
| 1 | Unverifiable; broken links; no citations |

### 10. Peer Review & Editorial Standards (Weight: 9%)

**Evaluate:** Journal impact, editorial independence, predatory journal flags.

| Score | Indicators |
|-------|-----------|
| 5 | Rigorous peer review; reputable editorial board |
| 3 | Editorial review but limited peer scrutiny |
| 1 | Predatory journal; no editorial oversight |

**Check:** Beall's List successors, DOAJ, journal impact factor (contextual, not definitive).

### 11. Perspective Diversity (Weight: 6%)

**Evaluate:** Unique viewpoint vs echo chamber repetition.

| Score | Indicators |
|-------|-----------|
| 5 | Offers distinct, evidence-based perspective |
| 3 | Standard viewpoint; adds some unique data |
| 1 | Echoes common narrative without new evidence |

### 12. Overall Integrity (Weight: 6%)

**Evaluate:** Holistic assessment — would you stake a pivotal claim on this source alone?

| Score | Indicators |
|-------|-----------|
| 5 | Yes, for pivotal claims (with normal verification) |
| 3 | Supporting evidence only |
| 1 | Never for factual claims |

---

## Composite Rating Bands

| Composite Score | Rating | Usage Guidance |
|----------------|--------|----------------|
| ≥ 4.2 | **High** | Primary evidence for pivotal claims |
| 3.5–4.1 | **Medium-High** | Supporting claims; verify pivotal findings |
| 2.8–3.4 | **Medium** | Use with caveats; corroborate key claims |
| 2.0–2.7 | **Medium-Low** | Illustrative only; corroborate all facts |
| < 2.0 | **Low** | Narrative/testimony value only |

---

## Worked Example

**Source:** Industry-funded think tank report on market size

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Provenance | 3 | Known think tank, not academic |
| Recency | 4 | Published 2025 |
| Methodology | 2 | Survey methodology unclear, no raw data |
| Corroboration | 2 | Cited by news but not independently verified |
| Conflicts | 1 | Funded by industry trade group |
| Framing | 2 | Optimistic language throughout |
| Evidential weight | 3 | Some data tables but selective |
| Counter-evidence | 1 | Ignores contradictory government data |
| Reproducibility | 2 | Summary only, no underlying data |
| Peer review | 1 | Not peer-reviewed |
| Perspective | 3 | Industry viewpoint, expected |
| Overall | 2 | Illustrative of industry narrative only |

**Composite:** ~2.3 → **Medium-Low** — Use only with explicit caveat; corroborate all statistics.

---

## Source Type Defaults

When manual scoring is impractical, use type defaults from `source_credibility_scorer.py`:

- `peer_reviewed_journal` — baseline Medium-High
- `government_official` — baseline High
- `primary_document` — baseline Medium-High
- `think_tank_report` — baseline Medium (check funding)
- `quality_journalism` — baseline Medium
- `preprint` — baseline Medium-Low (not replicated)
- `blog_opinion` — baseline Medium-Low
- `social_media` — baseline Low

Always override defaults when specific evidence warrants it.
