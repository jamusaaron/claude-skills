# Uncertainty and calibration

Load this in **Phase 7**. Pair every pivotal claim with `scripts/confidence_calibrator.py`. Overconfidence is the cardinal error of this skill.

## Bands

| Band | Range | When it is allowed |
|------|-------|--------------------|
| Very High | >90% | Almost never. Script hard-caps unless primary + ≥2 clusters + agreement ≥0.8 |
| High | 70–90% | Repeated independent measurement, transparent methods, stable over time |
| Medium | 50–70% | Default for messy policy/market/scientific-frontier questions |
| Low | 30–50% | Thin or conflicting evidence; still worth stating as a lead |
| Very Low | <30% | Speculation, zero sources, or pure forecast without base rate |

The calibrator **caps** scores. Do not add "but I feel sure" points. If you disagree with a cap, you are probably the bias.

## Inputs to the calibrator (honest values)

| Flag | Honest encoding |
|------|-----------------|
| `--n-sources` | Count of *independent* supporting items after clustering, not URLs |
| `--agreement` | Supporting / (supporting + contradicting) among medium+ sources. Ignore Low blogs in the ratio *or* disclose that you included them |
| `--source-quality` | Mean integrity /100 (High≈0.9, Medium≈0.6, Low≈0.3) |
| `--recency` | 1.0 if all key sources inside the window; 0.3 if the last measurement is years outside |
| `--independent-clusters` | Distinct institutions/datasets (not distinct domains of one agency) |
| `--has-primary` | Statute, judgment, microdata, paper, filing, instrument — not a news write-up of those |
| `--methods-transparent` | You could recompute or re-identify the result from public methods |
| `--contested` | Polarized public debate *or* genuine expert split |
| `--claim-type` | Must match the ledger type. Forecasts and values cap at Medium |

## What would change this

Every claim in the report needs 2–5 kill-switches. The script emits a default list; edit them to be *specific*:

- Bad: "new evidence"
- Good: "an RCT in population P with N>X and a pre-registered primary endpoint showing an effect including zero"

If you cannot name a kill-switch, you are defending an identity, not a claim.

## Missing data

Handle explicitly. Do not silently drop.

| Situation | Move |
|-----------|------|
| Series breaks / definition change | Do not splice without a note; treat as two claims |
| Paywalled primary | Mark unverified; seek repository, FOI, or author PDF; else cap reproducibility |
| Redacted legal / classified | State the hole; do not fill with punditry |
| Non-response / selection | Direction of bias if known; else widen the band one step |
| "No studies" | Distinguish "not searched" vs "searched these queries and found none" |

## Calibration hygiene

Internally (research log, then case log):

1. Before synthesis, write a number for the top 3 claims.
2. After verification loop, write the number again.
3. If the number rose without new independent evidence, you inflated. Reset.

Track a simple Brier-like honesty: when you said High, did later primaries agree? If you keep missing, your "High" is really Medium. Lower the prior in the next case log.

## Language that matches bands

| Band | Allowed verbs |
|------|----------------|
| High | "The measured series shows", "the statute requires" |
| Medium | "The best available evidence is consistent with" |
| Low | "A lead, not established:" |
| Very Low | "Unsupported / unknown given current public sources" |

Forbidden at Medium or below: "proves", "settled", "no doubt".

## Claim-type caps (same as script)

- `forecast`: cap 65 unless you have a scored base rate / backtest (still not a fact).
- `value`: cap 65; report as stakeholder mapping.
- `interpretation`: extra −6 in the raw score.
- `fact` without primary: −5 and cap 78.

## Decision use

Decision-makers often want a single percentage for the whole memo. Refuse. Give:

- Claim-level bands
- The one or two claims that actually change the decision
- The cheapest observation that would flip those claims

That is calibrated advice. A fake 87% on a blended narrative is not.
