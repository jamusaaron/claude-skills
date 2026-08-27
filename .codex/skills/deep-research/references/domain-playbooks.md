# Domain Playbooks

Specialized research guidance for common domain types. Load the relevant section when query maps to a domain.

---

## Scientific / Medical Research

### Source Priorities

1. Systematic reviews and meta-analyses (Cochrane, PubMed)
2. Peer-reviewed primary research (RCTs > observational)
3. Regulatory agency guidance (FDA, EMA, TGA, WHO)
4. Clinical trial registries (ClinicalTrials.gov)
5. Preprints (with explicit unreplicated caveat)

### Key Considerations

- **Hierarchy of evidence:** Systematic review > RCT > cohort > case-control > case series > expert opinion
- **Preprint handling:** Label as unreplicated; downgrade confidence one band
- **Predatory journals:** Check DOAJ, think-check-submit.org; verify editorial board
- **Statistical literacy:** Require sample size, confidence intervals, p-values in context
- **Conflicts:** Pharma funding common; check ICMJE disclosure standards

### Verification Targets

- Effect sizes and confidence intervals (not just p-values)
- Replication status
- Population studied vs population of interest
- Adverse events and limitations sections

### Common Pitfalls

- Citing abstract conclusions without reading methods
- Treating preprints as peer-reviewed
- Ignoring publication bias (negative results less published)
- Confusing statistical significance with clinical/practical significance

---

## Legal / Regulatory Research

### Source Priorities

1. Primary law (statutes, regulations, binding court decisions)
2. Official regulatory guidance and enforcement actions
3. Legislative history and explanatory memoranda
4. Tribunal/court decisions (binding vs persuasive authority)
5. Law review and practitioner commentary (secondary)

### Key Considerations

- **Jurisdiction:** Always specify applicable jurisdiction; distinguish binding vs persuasive
- **Black letter vs practice:** Law on books vs enforcement reality
- **Temporal:** Note if law has been amended; check commencement dates
- **Hierarchy:** Constitution > statute > regulation > guidance > commentary
- **Case law evolution:** Track whether decisions have been overturned on appeal

### Verification Targets

- Exact statutory text (not summaries)
- Jurisdiction and date of decision
- Whether decision is binding or persuasive in relevant jurisdiction
- Pending appeals or legislative amendments

### Common Pitfalls

- Citing non-binding foreign law as applicable
- Relying on law firm marketing alerts without reading primary source
- Ignoring recent amendments
- Confusing regulatory guidance with binding law

---

## Business / Market Research

### Source Priorities

1. SEC/company filings (10-K, 10-Q, annual reports)
2. Official market data (government statistics, trade associations)
3. Industry analyst reports (note methodology and conflicts)
4. Customer review aggregators (G2, App Store, Trustpilot)
5. Competitor primary sources (pricing pages, job postings, press releases)

### Key Considerations

- **Market size claims:** Trace to methodology; vendor-funded reports inflate
- **Competitive intelligence:** Use `competitive-teardown` skill for structured analysis
- **Financial data:** Prefer audited filings over press releases
- **Projections vs facts:** Label forecasts clearly as inference
- **Survivorship bias:** Failed companies excluded from "success" analyses

### Verification Targets

- Revenue/growth figures against SEC filings
- Market share claims against independent data
- Product feature claims against primary product pages
- Customer satisfaction against review sample size and selection

### Cross-Skill Integration

- `competitive-teardown` — Feature matrices, SWOT, positioning
- `competitive-intel` — Battlecards, win/loss analysis
- `financial-analyst` — DCF, ratio analysis, forecasting
- `saas-metrics-coach` — SaaS-specific metrics validation

---

## Policy / Government Research

### Source Priorities

1. Legislation and regulatory text
2. Government agency reports and official statistics
3. Parliamentary/congressional inquiries and submissions
4. International body reports (UN, OECD, World Bank, IMF)
5. Think tank analyses (note ideological positioning)

### Key Considerations

- **Federal vs state/local:** Jurisdiction matters; note interactions
- **Policy vs implementation:** Announced policy vs actual enforcement
- **Stakeholder submissions:** Public consultation responses reveal positions
- **Think tank bias:** Map funding and ideological positioning
- **International comparisons:** Context matters; don't assume transferability

### Verification Targets

- Policy text vs media reporting of policy
- Implementation timelines vs announcements
- Budget allocations vs policy rhetoric
- Impact evaluations (if available)

### Temporal Handling

Policy landscapes change rapidly. Always qualify with "as of [date]" and note pending legislation or reviews.

---

## Technology / Emerging Topics

### Source Priorities

1. Primary technical documentation and specifications
2. Peer-reviewed CS/engineering papers
3. Open-source repositories and issue trackers
4. Standards body documents (IETF, W3C, ISO)
5. Conference proceedings (NeurIPS, ICML, etc.)

### Key Considerations

- **Hype cycle:** Separate demonstrated capability from marketing claims
- **Benchmark validity:** Check benchmark methodology and cherry-picking
- **Reproducibility:** Code available? Results replicated?
- **Rapid obsolescence:** Flag recency explicitly; tech moves fast
- **Vendor demos vs production:** Distinguish staged demos from deployed systems

### Verification Targets

- Performance claims against independent benchmarks
- "State of the art" claims against actual leaderboard data
- Security claims against disclosed CVEs and audit reports
- Adoption claims against verifiable usage metrics

---

## Contested / Polarized Topics

### Mandatory Protocol

1. **Steelman all major positions** (see synthesis-patterns.md)
2. **Verification loop on top 3-5 claims** from each side
3. **Evidential weight, not equal time** — 95% consensus gets proportional weight
4. **Label influence vs evidence** — "This narrative is influential but lacks high-integrity evidence"
5. **Avoid moralizing** — Let evidential disparity speak

### Source Portfolio for Contested Topics

- Minimum 2 high-integrity sources per major position
- Include outlier voices with explicit tier labeling
- Search specifically for disconfirming evidence for your emerging conclusion
- Document shared-provenance clusters

### Output Requirements

- State "Evidence assessment as of [date]"
- Include steelman sections for each major position
- Assign confidence bands with explicit drivers
- Note where evidence is genuinely insufficient for resolution

---

## Information-Scarce Domains

When evidence is sparse:

1. **State sparsity explicitly** — Don't fill gaps with speculation
2. **First-principles bounds** — What can be inferred from established mechanisms?
3. **Historical analogs** — Similar past situations (label as analog, not proof)
4. **Counterfactual reasoning** — What would we expect if X were true?
5. **Recommended primary research** — Specific data sources, FOI strategies, expert consultations
6. **Wide confidence bands** — Default to Low or Medium confidence

Use uncertainty ladder prominently. Recommend follow-up rather than over-confident synthesis.
