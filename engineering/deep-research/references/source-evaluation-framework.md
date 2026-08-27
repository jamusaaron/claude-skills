# Source evaluation framework

Load this in **Phase 4**. Score every non-trivial source before it enters the claim ledger. Numeric scores are produced by `scripts/source_scorer.py`; this document is the rubric the script encodes.

Do not substitute a vibe rating ("seems legit") for the 12 dimensions. A source may be famous and still fail methodology, conflicts, or corroboration.

## Score scale

Each dimension is 0–10.

| Score | Meaning |
|------:|---------|
| 0–2 | Disqualifying for factual use |
| 3–4 | Weak; usable only as narrative or hypothesis |
| 5–6 | Mixed; needs a second independent leg |
| 7–8 | Solid for triangulation |
| 9–10 | Anchor-grade on this dimension |

The script computes a **weighted 0–100** and a band:

| Band | Score | Allowed use |
|------|------:|-------------|
| High | ≥85 | Anchor; may support a pivotal claim if one independent corroborator exists |
| Medium-High | 70–84 | Supporting citation; triangulate before treating as established |
| Medium | 55–69 | Context / stakeholder view; never sole support for a pivotal fact |
| Medium-Low | 40–54 | Narrative only until two high-integrity independents exist |
| Low | <40 | Quote as a *claim about a claim*. Never as evidence of fact |

Weights (must match the script): provenance 1.2, recency 0.9, methodology 1.3, corroboration 1.3, conflicts 1.1, framing 0.8, evidential weight 1.3, counter-evidence 1.0, reproducibility 1.0, editorial 0.9, perspective diversity 0.7.

## The 12 dimensions

### 1. Provenance and authority

Who produced this, and what is their track record?

- **9–10**: Named institution with a public error-correction record; named expert with domain publications; official gazette / statistical agency / court.
- **6–8**: Reputable specialist outlet; known researcher; government unit below national statistics office.
- **3–5**: Advocacy shop, trade body, or unaudited "institute".
- **0–2**: Anonymous blog, impersonation risk, or history of retractions without correction.

**Red flags:** sockpuppet institutes; "Dr" with unrelated doctorate; domain registered last month; author name that only exists on this page.

### 2. Recency and relevance

Temporal fit to the scoped window, not "newer is always better".

- Foundational methods papers can score high on relevance even if old — score recency separately from relevance in notes.
- For fast-moving policy, law, markets, and security: a 24-month half-life is the default (`--half-life-days 730`).
- For geology, language history, or settled physical constants: extend the half-life; do not punish age.

Decision rule: if the claim is about *current* state, a pre-window source may be used only as baseline, labelled "as of YEAR".

### 3. Methodological transparency

Can a sceptical reader see how the number or finding was produced?

| Design | Default ceiling until methods are inspectable |
|--------|-----------------------------------------------|
| Official census / admin data with published methodology | 9 |
| Pre-registered RCT / systematic review | 8–9 |
| Observational with identification strategy | 6–8 |
| Survey without sampling frame | 4 |
| "Internal data" / "our analysis shows" | 2–3 |
| Anecdote, composite character, unnamed sources only | 1–2 |

Score the *methods you can see*, not the methods you assume a famous author used.

### 4. Corroboration

Independent replication or convergence — not three outlets rewriting the same wire story.

Independence tests (need ≥2 to count as a second cluster):

- Different dataset or instrument
- Different institution and funding
- Different jurisdiction or time window
- Different method (qualitative vs quantitative vs documentary)

**Citation laundering:** A cites B cites C cites A. Treat the cluster as *one* source.

### 5. Funding and conflicts

Higher score = cleaner / better disclosed. Follow the money, then the incentives.

- Disclosed funder + independent analysis: 8–10
- Industry-funded but methods open and registered: 5–7
- Undisclosed overlapping interest: 0–3
- The source *is* the interested party (vendor white paper, litigant press release): cap at 4 unless used as primary testimony about their own position

### 6. Framing and language

Loaded verbs, missing comparators, false dichotomies, straw-men.

Examples that dock this dimension:

- "Soaring crime" without rate, base, and window
- "Safe and effective" as a slogan rather than a quantified risk/benefit
- "Experts agree" without a named body and dissent rate

Advocacy sources can still score well here if they label their values and steelman the other side.

### 7. Evidential weight

Quality *and* quantity of supporting data versus assertion.

- Microdata, full time series, or primary legal text: 8–10
- Summary statistic with denominator, sample, and uncertainty: 6–8
- Relative risk without baseline: 3–5
- Adjective ("robust", "significant") without number: 0–2

### 8. Counter-evidence handling

Does the source engage contradictory findings, or disappear them?

- Reports nulls, limitations, and rival studies: 8–10
- Mentions then straw-mans rivals: 4–6
- Silence on a well-known conflicting result: 0–3

### 9. Accessibility and reproducibility

Can claims be re-derived from cited materials without special access?

Paywalls are not a moral failing; *unverified paywalled extracts* are. If you cannot open it, either find an open version or mark the extract as unverified and cap this dimension at 4.

### 10. Peer review and editorial standards

| Venue | Default |
|-------|---------|
| Statutory instrument, court, official statistics | 8 (not "peer review" but public process) |
| Journal with named editors, corrections policy | 7–9 |
| Preprint | 4 until reviewed |
| Newspaper with corrections desk | 6 |
| Newsletter / Substack | 2–4 |
| Predatory / hijacked journal | 0–1 |

### 11. Diversity of perspective

A high score here means the source adds a *non-redundant* viewpoint — not that it is "balanced" in the false-equivalence sense. An echo of the last four sources scores 2. A well-evidenced minority methods critique scores 8.

### 12. Overall integrity (derived)

Do not type this by hand. Use the weighted score. Add a one-sentence justification in the source ledger: *which two dimensions dominate, and one residual risk*.

## Worked examples

**A. National statistical agency labour-force release (HTML + PDF, dated last month, methods note linked).**  
Prior type `government`. Recency 10. Provenance 9. Methodology 8. Conflicts 7. Band typically **High / Medium-High**. Use as anchor for the *measured series*, not for causal stories journalists hang on it.

**B. Vendor blog "we reduced churn 40% with AI".**  
Type `corporate`. Conflicts 3. Methodology 2 (no definition of churn, no holdout). Band **Low / Medium-Low**. Allowed use: vendor *claim*. Not evidence of efficacy.

**C. Preprint RCT, protocol on OSF, industry funded, not yet reviewed.**  
Type `preprint` + `--discloses-funding` + `--open-data`. Band often **Medium**. Pivotal medical-adjacent claims still need a systematic review or regulator label; this is a lead.

**D. Viral thread with a screenshot of a table.**  
Type `social`. Band **Low**. Extract the alleged primary (the table's real URL) and score *that*. The thread is testimony about circulation, not about the table.

## Domain variants

Use these *adjustments*, not a different rubric.

- **Science:** overweight methodology, reproducibility, counter-evidence. Preprints default Medium until methods hold.
- **Law:** primary text (statute, judgment) beats commentary. Score commentary as interpretation. Forum and date are part of provenance.
- **Policy:** distinguish instrument text, implementation data, and advocacy evaluation. Think tanks are `ngo_thinktank` until proven otherwise.
- **Markets:** filings and prices beat TAM slides. Score sell-side research with a conflicts penalty.
- **Medicine / public health (non-diagnostic):** prefer systematic reviews and regulator labels over single trials. Absolute risk required. This skill does not diagnose or prescribe.
- **OSINT:** provenance includes chain of custody, geolocation, and reverse-image search. A single unverified clip caps evidential weight at 3.

## Red-flag catalogue (script `--red-flag`)

| Flag | Dimension hit | Typical deduction |
|------|---------------|-------------------|
| `retracted` | provenance | 6 |
| `predatory` | editorial | 7 |
| `undisclosed_funding` | conflicts | 5 |
| `anonymous` | provenance | 4 |
| `paywalled_unverified` | reproducibility | 3 |
| `single_anecdote` | evidential_weight | 5 |
| `loaded_language` | framing | 3 |
| `no_methods` | methodology | 4 |
| `circular_citation` | corroboration | 4 |

Low-integrity sources are **kept** when they document an influential narrative. Label them: "widely circulated claim; not established."

## Decision rules

1. If band ≤ Medium-Low, the source cannot be the sole support of a `fact` claim.
2. If two High sources conflict, do not average them. Classify the dispute (see `claim-graph-and-triangulation.md`).
3. If you cannot fill methodology *and* corroboration, you do not have a finding; you have a lead.
4. Run `source_scorer.py` and paste the JSON `justification` into the source ledger. Do not round bands upward.
