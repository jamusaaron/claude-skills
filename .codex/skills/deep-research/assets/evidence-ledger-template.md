# Evidence Ledger

**Research Topic:** [Topic]  
**Date Started:** [YYYY-MM-DD]  
**Last Updated:** [YYYY-MM-DD]  
**Total Entries:** [N]

Running log of all sources acquired during research. Update after Phase 3 (deep acquisition) and Phase 4 (scoring).

---

## Ledger Entries

### [S001] [Source Title]

| Field | Value |
|-------|-------|
| **URL/DOI** | |
| **Type** | [ ] Peer-reviewed  [ ] Government  [ ] Primary doc  [ ] Think tank  [ ] Journalism  [ ] Preprint  [ ] Blog  [ ] Social |
| **Tier** | [ ] 1  [ ] 2  [ ] 3  [ ] 4  [ ] 5 |
| **Date** | [Publication date] |
| **Authors/Org** | |
| **Credibility Rating** | [ ] High  [ ] Medium-High  [ ] Medium  [ ] Medium-Low  [ ] Low |
| **Composite Score** | [X.X / 5.0] |
| **Flags** | [None / list flags] |

**Key claims extracted:**

1. [Claim 1 — verbatim or close paraphrase with page/section ref]
2. [Claim 2]
3. [Claim 3]

**Maps to sub-questions:** [SQ1, SQ3]

**Maps to hypotheses:** [H1]

**Cross-references:** [Related source IDs: S003, S007]

**Notes:** [Methodology concerns, funding, caveats]

---

### [S002] [Source Title]

| Field | Value |
|-------|-------|
| **URL/DOI** | |
| **Type** | |
| **Tier** | |
| **Date** | |
| **Authors/Org** | |
| **Credibility Rating** | |
| **Composite Score** | |
| **Flags** | |

**Key claims extracted:**

1. 
2. 

**Maps to sub-questions:** 

**Maps to hypotheses:** 

**Cross-references:** 

**Notes:** 

---

### [S003] [Source Title]

| Field | Value |
|-------|-------|
| **URL/DOI** | |
| **Type** | |
| **Tier** | |
| **Date** | |
| **Authors/Org** | |
| **Credibility Rating** | |
| **Composite Score** | |
| **Flags** | |

**Key claims extracted:**

1. 
2. 

**Maps to sub-questions:** 

**Maps to hypotheses:** 

**Cross-references:** 

**Notes:** 

---

## Quick Reference Index

| ID | Title (short) | Rating | SQ Coverage | Pivotal Claims |
|----|--------------|--------|-------------|----------------|
| S001 | | | SQ1, SQ3 | C1, C2 |
| S002 | | | SQ2 | |
| S003 | | | SQ1, SQ2, SQ4 | C3 |

---

## Shared-Provenance Tracker

| Origin | Source IDs | Counted As |
|--------|-----------|------------|
| [Press release / study / dataset] | S001, S004, S008 | 1 for corroboration |

---

## Acquisition Log

| Date | Action | Source ID | Result |
|------|--------|-----------|--------|
| | Searched: [query] | S001 | Found / Paywalled / Not found |
| | Browsed: [URL] | S002 | Extracted / Truncated / Error |
| | Verified: [claim] | S001, S003 | Confirmed / Modified |

---

## Gap Tracker

| Sub-Question | Sources Mapped | High-Integrity Count | Gap Status |
|-------------|---------------|---------------------|------------|
| SQ1 | S001, S003 | 2 | Covered |
| SQ2 | S002 | 0 | **Gap — needs high-integrity source** |
| SQ3 | — | 0 | **Gap — no coverage** |

---

*Score batch: `python3 scripts/source_credibility_scorer.py sources.json --format text`*  
*Analyze gaps: `python3 scripts/research_gap_analyzer.py coverage.json --format text`*
