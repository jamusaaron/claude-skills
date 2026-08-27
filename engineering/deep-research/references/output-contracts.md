# Output contracts

Load this in **Phase 8**. Every delivery uses the same bones; depth scales with tier. Templates live in `assets/`. Assemble mechanically with `scripts/report_assembler.py`, then edit for prose — do not let the assembler be the only voice, and do not let prose invent claims absent from the ledger.

## Citation format (platform-agnostic)

Default, portable:

- In-body: claim id plus locator — `Admissions fell 4.2% YoY [C1; S3; https://example.gov/lfs]`.
- If the host platform provides native citation chips / `render_inline_citation` / footnote plugins, **use them in addition to** claim IDs, not instead of them.
- Never a bare "according to experts" with no locator.
- Dates on every factual sentence that can go stale.

## Required layers

### 1. Executive briefing (150–300 words)

Must include: core answer, claim-level confidence (not one fake report %), 3–5 implications, one-sentence scope/limit. Suitable for a decision-maker who will not read further. Must not contain unsourced numbers.

Template: `assets/executive-briefing.md`.

### 2. Key findings

Bullet hierarchy grouped by Phase 1 sub-questions. Each bullet:

`claim + [C# / locators] + source note + confidence band + 1–2 sentence rationale`

No orphan insights that are not in the ledger.

### 3. Detailed analysis

Thematic or chronological. Tables for comparisons. Keep mechanisms in `mechanism` claims. Use `assets/full-research-report.md`.

### 4. Claim ledger

Table or embedded markdown from `claim_ledger.py export-md`. This is the audit spine.

### 5. Source appendix

| ID | Type | Band | Date | Title | URL | Key contribution | Limitation |

### 6. Limitations, unknowns, monitoring

Gaps, volatility, alternative interpretations, cheapest next observation. Include **as-of** stamp. For fast domains: "Public sources may have shifted since {date}."

### 7. Actionables

Decision-grade, scoped, reversible where possible. Tie each action to a claim id. If the user asked only for understanding, label this section "If you were deciding…".

## Format variants (same contract, different compression)

| Variant | Use | Cuts |
|---------|-----|------|
| Executive briefing only | R0/R1, light tier, time-boxed | Layers 3–5 become links/appendix |
| Decision memo | R1 operational | Lead with actionables; analysis in appendix |
| Scholarly | Scientific lens | Methods and search log more visible; still keep exec layer |
| Adversarial dossier | R3 | Steelman annex + red-team annex mandatory |

## Quality gates (block delivery if any fail)

- Every non-obvious `fact` has ≥N independent medium+ sources (N from tier).
- Medium-Low / Low sources used only as narrative, labelled.
- Contested claims classified (factual / interpretive / value).
- `citation_integrity.py` exits 0 or remaining errors are listed in Limitations with reasons.
- `bias_audit.py` is not `fail`, or failures are addressed in prose.
- No Very High confidence without calibrator caps satisfied.
- Tone: precise, non-moralizing, no false equivalence.

## What not to ship

- Raw SERP dumps
- Unscored PDFs summarized from memory
- "Could go either way" as a substitute for a classified conflict
- Legal advice, diagnosis, or instructions to cause harm (decline; see SKILL.md)

## Self-assessment block (internal or appendix)

Score 1–5: coverage, traceability, steelman quality, calibration, bias resistance, efficiency. Copy into `assets/case-log.md`.
