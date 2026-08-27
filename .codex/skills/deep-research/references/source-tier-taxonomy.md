# Source Tier Taxonomy

Prioritize sources by evidential weight. Use during Phase 2 (horizon scanning) to ensure portfolio diversity.

---

## Tier Definitions

### Tier 1 — Primary / Gold Standard

**Definition:** Original data, documents, or firsthand records. Highest evidential weight.

| Source Type | Examples | Default Rating |
|-------------|----------|----------------|
| Raw datasets | ABS, census, clinical trial data, SEC filings | High |
| Legislation | Statutes, regulations, court judgments | High |
| Official statistics | Government agencies, central banks, WHO | High |
| Peer-reviewed primary research | Original studies with methods and data | High |
| Institutional primary records | Annual reports, audit findings, FOI releases | High |

**Usage:** Suitable for pivotal claims. Still apply 12-point scoring for methodology and conflicts.

### Tier 2 — High-Quality Secondary

**Definition:** Rigorous analysis, synthesis, or reporting built on primary sources.

| Source Type | Examples | Default Rating |
|-------------|----------|----------------|
| Systematic reviews / meta-analyses | Cochrane, Campbell Collaboration | High |
| Government reports | Productivity Commission, GAO, OECD | Medium-High to High |
| Law reviews / regulatory guidance | Official agency guidance documents | Medium-High |
| Investigative journalism | Named sources, original documents cited | Medium-High |
| Academic textbooks / handbooks | Established disciplinary consensus | Medium-High |

**Usage:** Strong supporting evidence. Verify pivotal statistics against Tier 1 when possible.

### Tier 3 — Expert & Institutional Commentary

**Definition:** Expert opinion, institutional positions, or professional analysis.

| Source Type | Examples | Default Rating |
|-------------|----------|----------------|
| Think tank reports | Brookings, RAND, CIS (note funding) | Medium |
| Industry analyst reports | Gartner, Forrester (note vendor ties) | Medium |
| Expert testimony | Congressional testimony, conference keynotes | Medium |
| Professional body statements | Medical associations, bar associations | Medium-High |
| Quality news analysis | In-depth reporting with named experts | Medium |

**Usage:** Context and interpretation. Corroborate factual claims with Tier 1-2.

### Tier 4 — Tertiary & Aggregated

**Definition:** Summaries, compilations, or reporting of reporting.

| Source Type | Examples | Default Rating |
|-------------|----------|----------------|
| News aggregation | Google News snippets, Wikipedia (verify refs) | Medium-Low |
| Preprints (unreplicated) | arXiv, bioRxiv without peer review | Medium-Low |
| Trade publications | Industry magazines, vendor whitepapers | Medium-Low |
| Encyclopedia entries | Verify against primary references | Medium-Low |
| Conference abstracts | Without full paper | Medium-Low |

**Usage:** Discovery and leads only. Never sole evidence for pivotal claims.

### Tier 5 — Narrative & Testimony

**Definition:** Personal accounts, social discourse, opinion without rigorous backing.

| Source Type | Examples | Default Rating |
|-------------|----------|----------------|
| Social media posts | X/Twitter, LinkedIn, Reddit | Low |
| Opinion blogs | Personal blogs, Substack without data | Low |
| Anonymous forums | 4chan, anonymous Reddit | Low |
| Press releases (uncorroborated) | Corporate PR without independent verification | Medium-Low |
| Testimonial / anecdote | Individual experience stories | Low (as standalone fact) |

**Usage:** Illustrate narratives, sentiment, emerging discourse. Always corroborate factual claims. Excellent for identifying "outlier voices" and real-time context.

---

## Portfolio Diversity Requirements

Minimum source type diversity by research depth:

| Depth | Min Tier 1-2 | Min Source Types | Max Tier 5 as % of Total |
|-------|-------------|------------------|--------------------------|
| Light | 2 | 2 | 30% |
| Medium | 5 | 3 | 20% |
| Deep | 10 | 4 | 15% |

**Automate gap detection:** `python3 scripts/research_gap_analyzer.py coverage.json`

---

## Domain-Specific Tier Adjustments

### Scientific / Medical

- Tier 1: RCTs, systematic reviews, regulatory trial data
- Tier 2: Peer-reviewed observational studies
- Tier 4: Preprints (until replicated)
- Avoid: Supplement marketing, predatory journals

### Legal / Regulatory

- Tier 1: Statutes, regulations, binding court decisions
- Tier 2: Official regulatory guidance, law review
- Tier 3: Practitioner commentary, law firm alerts
- Avoid: Non-jurisdiction commentary presented as binding

### Business / Market

- Tier 1: SEC filings, audited financials, official market data
- Tier 2: Industry reports with disclosed methodology
- Tier 4: Vendor whitepapers, sponsored research
- Avoid: Anonymous forum stock tips

### Policy / Government

- Tier 1: Legislation, official statistics, agency reports
- Tier 2: Parliamentary inquiries, Ombudsman reports
- Tier 3: Think tank analysis (note ideological positioning)
- Avoid: Partisan op-eds without data

---

## Source Selection Decision Tree

```
New source discovered
│
├─ Is it Tier 1 (primary)? ──YES──► Acquire fully; score with 12-point framework
│
├─ Is it Tier 2-3? ──YES──► Extract key claims; trace pivotal stats to Tier 1
│
├─ Is it Tier 4? ──YES──► Use as lead only; find Tier 1-2 corroboration
│
└─ Is it Tier 5? ──YES──► Log for narrative/sentiment; never sole evidence
    │
    └─ Corroborate any factual claims before inclusion in synthesis
```

---

## Shared-Provenance Detection

Multiple sources may trace to a single origin. Treat as ONE source for corroboration.

**Signals:**
- Same press release quoted across outlets
- Same study cited without independent analysis
- Same dataset referenced without new analysis
- Syndicated content across news networks

**Fix:** Trace to primary origin. Count primary once. Use `claim_evidence_mapper.py` to detect domain clustering.

---

## Anchor vs Outlier Sources

| Type | Purpose | Tier Target |
|------|---------|-------------|
| **Anchor sources** | Establish baseline consensus; high integrity, recent, transparent | Tier 1-2 |
| **Outlier voices** | Capture contrarian or emerging perspectives | Any tier, with explicit caveat |
| **Bridge sources** | Connect domains or translate between audiences | Tier 2-3 |

A healthy portfolio has 60-70% anchor sources, 20-30% supporting/contextual, and 10-20% outlier (clearly labeled).
