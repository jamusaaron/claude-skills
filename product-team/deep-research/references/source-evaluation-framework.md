# Source Evaluation Framework (12-point rubric)

Score every non-trivial source. Use `scripts/source_credibility.py` to apply the numeric version; use this file to judge edge cases the script cannot see (ghost authorship, hijacked journals, quiet retractions).

Scores are **0–5 per dimension**. Integrity bands:

| Average | Band | Use |
|---------|------|-----|
| ≥ 4.4 | High | May carry pivotal claims; still needs a second lineage |
| ≥ 3.6 | Medium-High | Default workhorse evidence |
| ≥ 2.8 | Medium | Supporting only unless it is the unique primary text |
| ≥ 2.0 | Medium-Low | Narrative / color; caveat in-line |
| < 2.0 | Low | Illustrative of a discourse, never of a fact |

A **primary source** (statute, dataset, filing, judgment, lab paper) can outrank a High-band secondary even if the average is slightly lower — flag it as `primary: true`.

## The 12 dimensions

### 1. Provenance & authority
Who produced this, and what is their track record?

- 5: Named expert or institution with relevant mandate; no retraction history on this topic
- 3: Reputable outlet, author only loosely qualified
- 1: Anonymous, credential-inflated, or serial misinformation host
- **Watch:** .edu ≠ quality (student pages, abandoned labs). .org ≠ nonprofit neutrality.

### 2. Recency & relevance
Does the *vintage* match the claim?

- Stamp every number with an as-of date.
- Foundational methods papers can be old (mark `foundational: true`).
- Official statistics: prefer the latest *revision*, not the first release.
- 5: Within the decision window and measuring the same construct
- 1: Superseded, or right decade / wrong population

### 3. Methodological transparency
Could a skilled skeptic reconstruct the result?

Look for: sample, inclusion rules, identification strategy, power, preregistration, code/data.
Opinion essays score low here even when the author is famous.

### 4. Corroboration
Independent replication, not the same press release in 14 newspapers.

Use `scripts/citation_graph.py` + `scripts/claim_triangulator.py`. Same dataset + same funder + same authors = **one lineage**.

### 5. Funding & conflicts
Disclosed industry funding is not an automatic kill; **undisclosed** is.

Follow the money one hop: parent PAC, trade association, litigation funder, think-tank donor page.

### 6. Framing & language
Loaded terms, missing alternatives, false balance, straw men.

Script heuristic catches cartoon propaganda. You still need to catch sophisticated framing ("concerns have been raised" with no named raiser; "up to" statistics; denominator tricks).

### 7. Evidential weight
Assertion < anecdote < observational < well-identified causal < multiple designs converging.

n=12 executive interviews are data. They are not a prevalence statistic.

### 8. Counter-evidence handling
Does the source steelman the other side, ignore it, or pathologize it?

Limitations sections that only humble-brag ("our effect is so large that...") score poorly.

### 9. Accessibility & reproducibility
Can a reader get to the same artifact?

Paywalled is allowed if you cite the stable identifier (DOI, statute citation) and note the barrier. Unrecoverable screenshots of "internal data" score near 0.

### 10. Peer review & editorial standards
Peer review is a process, not a halo. Predatory / hijacked journals, unsolicited special issues, and "reviewed in 48 hours" are red flags.

Government statistical releases and supreme-court opinions are not peer-reviewed and can still be High on other dimensions.

### 11. Diversity of perspective
A source can be excellent and still be an echo. Track whether your *portfolio* of High sources spans methods and institutions, not just whether each source is "nice."

### 12. Self-reported caveats
Sources that hide uncertainty are more dangerous than sources that advertise it.

## Worked mini-examples

**A.** National statistics agency labour-productivity table, methods note published, open data, 11 months old → typically **High**. Weakness: may not match your occupation slice (Dimension 2 / 7).

**B.** Vendor "State of the Industry" survey, n=180 customers, leading questions, marketing URL → **Medium-Low**. Keep for hypothesis generation.

**C.** Anonymous Medium post, "secret data," no methods → **Low**. Use only to document a narrative's existence.

**D.** NBER working paper, serious DiD, not yet peer-reviewed → **Medium-High**, with preprint caveat. Do not upgrade to High solely because the authors are famous.

**E.** Systematic review, PRISMA, open code, but all included RCTs share one sponsor → **Medium** on corroboration even if methods=5.

## Scoring protocol

1. Auto-score with the script from URL + metadata flags.
2. Override dimensions you actually inspected (`dimension_scores` in the JSON).
3. Write a one-sentence justification (the script emits a draft).
4. If band ≤ Medium-Low, tag every downstream claim that used it.

## Independence test (run before triangulation)

Two URLs are **not** independent if they share any of:

- The same dataset / registry extract
- The same corresponding author or lab
- The same press embargo packet
- A citation-only relationship with no new measurement (B cites A and adds no data)

When in doubt, collapse them into one lineage id (`organization` or `dataset` field).
