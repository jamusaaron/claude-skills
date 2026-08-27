# Synthesis Patterns

Advanced analytical techniques for Phase 5 evidence synthesis. Combine multiple patterns for contested or high-stakes topics.

---

## Evidence Matrix Construction

Map every source to every research question/hypothesis.

### Matrix Structure

| | SQ1 | SQ2 | SQ3 | ... |
|---|-----|-----|-----|-----|
| Source A (High) | ●●● | ●● | — | |
| Source B (Med) | ●● | ●●● | ● | |
| Source C (Low*) | — | ● | ●● | |

**Legend:** ● = relevant evidence (more dots = stronger contribution); — = not relevant; * = credibility caveat required

**Weighting:** High=3, Medium-High=2, Medium=1, Medium-Low/Low=0.5 (illustrative only)

**Tool:** `python3 scripts/claim_evidence_mapper.py claims.json`

---

## Triangulation Patterns

### Convergent Triangulation

Multiple independent sources reach the same conclusion through different methods.

**Signal:** High confidence upgrade warranted.
**Verify:** Sources don't share common primary origin.

### Divergent Triangulation

Sources disagree — classify the disagreement:

| Type | Characteristics | Response |
|------|----------------|----------|
| **Factual** | Dispute over data, numbers, events | Resolve via primary data or targeted re-acquisition |
| **Interpretive** | Same data, different frameworks | Present both with evidential weight |
| **Value-laden** | Different normative assumptions | Map assumptions; indicate implications for user context |

### Methodological Triangulation

Combine quantitative + qualitative + documentary evidence on the same question.

**Example:** Statistics show trend (quantitative) + stakeholder interviews explain mechanism (qualitative) + policy documents show regulatory response (documentary).

---

## Steelman + Devil's Advocate

### Steelman (Mandatory for contested topics)

1. State the strongest version of Position A with its best evidence
2. State the strongest version of Position B with its best evidence
3. Identify where evidence converges
4. Identify where evidence diverges and why
5. Assign relative evidential weight (not equal time)

### Devil's Advocate (Internal verification)

After synthesis, argue against your own conclusion:
- What is the strongest counter-argument?
- What evidence would falsify the conclusion?
- What assumptions are you making?
- What would a skeptical expert object to?

**Template:** `assets/counter-argument-worksheet.md`

---

## Temporal Trend Analysis

Track how evidence, consensus, or policy has evolved.

### Steps

1. **Establish timeline** — Key events, publications, policy changes
2. **Map evidence shifts** — How did expert consensus change?
3. **Identify inflection points** — What triggered shifts?
4. **Note recency effects** — Is current discourse overweighting recent events?
5. **Project trajectory** — Based on trend, what is likely next? (Label as inference)

### Output Format

```
[Year] — [Event/Evidence] — [Impact on consensus]
...
Current state (as of [date]): [Summary]
Volatility assessment: [Stable / Evolving / Rapidly changing]
```

---

## Stakeholder Power-Interest Map

Identify who benefits, bears costs, and controls information flow.

| Stakeholder | Interest | Power/Influence | Information Control | Bias Risk |
|-------------|----------|-----------------|---------------------|-----------|
| [Group A] | [What they want] | High/Med/Low | [What they publish/control] | [Potential bias] |

**Use:** Contextualize source selection bias, explain narrative-data gaps, inform recommendations.

---

## Narrative vs Data Reconciliation

When stories conflict with statistics:

1. **Privilege data** for factual claims
2. **Explain narrative persistence:**
   - Media incentives (engagement > accuracy)
   - Lived experience vs population statistics
   - Measurement lags or definitional differences
   - Selection effects (survivor stories)
3. **Don't dismiss narratives** — they reveal sentiment, stakeholder experience, and information gaps
4. **Label clearly:** "Data shows X; narrative Y persists because Z"

---

## Scenario Planning (Layer 6)

For forward-looking queries where empirical data is limited.

### Three-Scenario Framework

| Scenario | Probability | Key Assumptions | Implications |
|----------|-------------|-----------------|--------------|
| **Base case** | Most likely | [Assumptions] | [Actions] |
| **Upside** | Possible | [What would need to be true] | [Actions] |
| **Downside** | Possible | [What would need to be true] | [Actions] |

**Rules:**
- Label all scenarios as inference, not fact
- Identify "signpost" events that would shift between scenarios
- Use pre-mortem on base case

---

## Verification Loop Protocol

Mandatory for medium+ depth on 3-5 pivotal claims.

### Loop Steps

1. **Select pivotal claims** — Highest impact on conclusion
2. **Check provenance** — Do supporting sources share origin?
3. **Re-acquire primary** — Browse/extract exact quotes and context
4. **Cross-check independent** — Find 1+ independent high-integrity source
5. **Document delta** — Did verification change confidence? How?
6. **Iterate or stop** — Diminishing returns → proceed; major delta → replan

### Verification Log Format

```
Claim: [statement]
Initial confidence: [band]
Verification action: [what you did]
Result: [confirmed / modified / falsified]
Updated confidence: [band]
Impact on synthesis: [none / minor / major]
```

---

## Synthesis Quality Checklist

Before delivering output:

- [ ] Evidence matrix complete (all sub-questions mapped)
- [ ] Pivotal claims verified (verification loop documented)
- [ ] Contested claims steelmanned with evidential weight
- [ ] Confidence bands assigned to all key findings
- [ ] Narrative-data conflicts reconciled
- [ ] Temporal context provided for evolving topics
- [ ] Bias audit completed
- [ ] Limitations and gaps explicitly stated

**Tool:** `python3 scripts/synthesis_outline_builder.py plan.json`
