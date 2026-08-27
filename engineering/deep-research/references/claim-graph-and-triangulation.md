# Claim graph and triangulation

Load this in **Phase 5**. Atomize prose into claims, attach evidence, and resolve conflicts *before* writing the report. The executable store is `scripts/claim_ledger.py`.

A report without a claim graph is a narrative. Narratives hide missing legs.

## Atomize

A **claim** is one falsifiable sentence. Split compound sentences.

| Bad (compound) | Good (atoms) |
|----------------|--------------|
| "The policy cut emissions and saved money, proving markets work." | C1 emissions effect (fact); C2 fiscal effect (fact); C3 "proving markets work" (interpretation / value) |
| "Experts say the drug is safe." | C1 named-body position (fact about a statement); C2 safety in a defined population (fact) — these are different claims |

Assign `type`:

| Type | Test | Corroboration |
|------|------|----------------|
| `fact` | Can be true or false given a definition, window, and population | ≥2 independent supporting items for standard+ tiers |
| `mechanism` | Causal / process story | Need identification, not just correlation |
| `interpretation` | What the facts *mean* | Steelman rivals; do not treat as fact |
| `forecast` | Future state | Scenario, not finding; cap confidence (see calibrator) |
| `value` | Ought / should | Map to stakeholder; never launder into fact |

IDs: `C1`, `C2`, … for claims; `E1`, … for evidence; `S1`, … for sources. Stable IDs survive rewrites.

## Graph structure

```
Claim (C#) ──supports── Evidence (E#) ──produced-by── Source (S#)
            ──contradicts──
            ──qualifies──
            ──context──
```

Rules:

- Evidence without a claim is an **orphan** (`citation_integrity.py` flags it).
- A claim without evidence is **unverified**.
- `qualifies` is not a fudge: use it for scope limits ("holds for adults, not children").
- `context` is background that must not be counted as support in status roll-up.

Ledger status is mechanical:

| Evidence mix | Status |
|--------------|--------|
| No links | `unverified` |
| Only context/qualifies | `insufficient` |
| Supports only | `supported` |
| Contradicts only | `refuted` |
| Supports + contradicts | `contested` |

Mechanical status is a **tripwire**, not the verdict. A `supported` claim with one Low-band blog is still unusable. Overlay integrity bands from Phase 4.

## Independence and triangulation

Triangulation is convergence across **methods, datasets, and institutions**, not across headlines.

Minimum independent legs by tier:

| Tier | Fact claim | Pivotal fact |
|------|------------|--------------|
| light | 1 primary **or** 2 secondary | 2 |
| standard | 2 independent medium+ | 2 + verification loop |
| deep / adversarial | 2 independent medium+ in ≥2 host clusters | same + red-team |

**Host cluster:** registrable domain, or `source_id` if no URL. `www.example.gov` and `data.example.gov` are one cluster if they are the same agency's CMS. Use judgment; when unsure, split.

**Three-source illusion:** wire copy → newspaper → aggregator. Score as one evidence item with three URLs, and pick the most primary locator.

## Conflict resolution protocol

When a claim is `contested`:

1. **Classify the dispute** (mandatory; do not "present both sides" as if they were the same kind of object):
   - **Factual:** numbers, dates, texts, measurements disagree. Resolve toward primary instruments (statute PDF, microdata, judgment, satellite, lab).
   - **Interpretive:** same facts, different models. Keep both; report which facts each model needs.
   - **Value:** disagreement about goals or rights. Map stakeholders; do not fake a factual winner.
2. **Check non-independence.** If both camps cite one lab or one FOI dump, you have one dataset and two sermons.
3. **Check scope mismatch.** Often "they disagree" is "they measured different windows/populations". Recode as two claims.
4. **Do not average.** A High primary and a Low blog do not make Medium. Drop the Low from the factual graph; retain it in the narrative appendix if it is influential.
5. **Write the residue.** If still contested after classification, the finding is the *contest*, with a confidence cap.

## Synthesis drift detector

Compare the Phase 1 restated query to the Phase 8 thesis in one paragraph.

Drift patterns:

- **Query swap:** user asked "does X work"; draft answers "people believe X works".
- **Scope creep:** extra geographies, extra years, extra moral claims.
- **Convenience peak:** early High source dominates later contrary primaries.
- **Smoothing:** contested claims rewritten as "mixed evidence" without naming the conflict class.

Fix: list each C# against the original sub-questions. Orphan findings that do not map back are either new sub-questions (replan) or cuts.

## Worked mini-graph

Query: "Did Program P reduce hospital admissions in 2024?"

- C1 (fact): All-cause admissions in region R fell YoY in 2024.
- C2 (fact): The fall is attributable to Program P.
- C3 (interpretation): P should be scaled nationally.

Evidence:

- E1 supports C1 — ministry statistical release (High).
- E2 qualifies C1 — fall concentrated in one age band.
- E3 contradicts C2 — difference-in-differences preprint (Medium) finds no effect after controls.
- E4 supports C2 — program office blog (Low). Drop E4 from C2's factual support; keep as stakeholder view.

Outcome: C1 supported; C2 contested (factual vs identification); C3 value, out of scope unless asked.

## Ledger commands (minimum path)

```bash
python scripts/claim_ledger.py init --path ledger.json --query "..."
python scripts/claim_ledger.py add-claim --path ledger.json --id C1 --statement "..." --type fact
python scripts/claim_ledger.py add-evidence --path ledger.json --id E1 --claim C1 --stance supports --url https://example.gov/x --date 2026-01-15 --band high
python scripts/claim_ledger.py status --path ledger.json --json
python scripts/claim_ledger.py contradictions --path ledger.json
python scripts/citation_integrity.py --ledger ledger.json --min-sources 2
```

Do not write Layer 2 (key findings) until `gaps` is empty *or* every remaining gap is disclosed in Limitations.
