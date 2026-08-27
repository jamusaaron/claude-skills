# Source Matrix

**Research Topic:** [Topic]  
**Date:** [YYYY-MM-DD]  
**Total Sources:** [N]  
**High-Integrity Sources:** [N]

---

## Summary Statistics

| Rating | Count | % of Total |
|--------|-------|------------|
| High | | |
| Medium-High | | |
| Medium | | |
| Medium-Low | | |
| Low | | |

| Source Type | Count |
|-------------|-------|
| Peer-reviewed journal | |
| Government official | |
| Primary document | |
| Think tank report | |
| Quality journalism | |
| Preprint | |
| Blog/opinion | |
| Social media | |

---

## Source Matrix

| ID | Title | Type | Date | Tier | Rating | Score | Key Contribution | Limitations | Relevance |
|----|-------|------|------|------|--------|-------|------------------|-------------|-----------|
| S1 | | | | 1-5 | High/Med/Low | /5.0 | | | High/Med/Low |
| S2 | | | | | | | | | |
| S3 | | | | | | | | | |
| S4 | | | | | | | | | |
| S5 | | | | | | | | | |

---

## Coverage Map (Sources × Sub-Questions)

| Source | SQ1 | SQ2 | SQ3 | SQ4 | SQ5 |
|--------|-----|-----|-----|-----|-----|
| S1 | ●●● | ●● | — | | |
| S2 | ●● | ●●● | ● | | |
| S3 | — | ● | ●● | ●●● | |

**Legend:** ● = relevant evidence (more = stronger); — = not relevant

---

## Shared-Provenance Clusters

| Cluster | Sources | Common Origin | Counted As |
|---------|---------|---------------|------------|
| | S1, S4, S7 | Same press release | 1 source for corroboration |

---

## Anchor vs Outlier Classification

### Anchor Sources (Tier 1-2, high integrity)

| ID | Title | Role |
|----|-------|------|
| | | Establishes baseline consensus |

### Outlier Sources (contrarian/emerging, with caveat)

| ID | Title | Role | Caveat |
|----|-------|------|--------|
| | | Captures dissenting view | |

---

## Flags & Actions Required

| Source ID | Flag | Action |
|-----------|------|--------|
| | potential_conflict_of_interest | Verify funding; corroborate claims |
| | limited_corroboration | Find independent source |
| | not_standalone_evidence | Illustrative only; corroborate all facts |

---

*Score sources: `python3 scripts/source_credibility_scorer.py sources.json --format text`*  
*Map claims: `python3 scripts/claim_evidence_mapper.py claims.json --format text`*
