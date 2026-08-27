# Output templates by stakeholder

Pair with `synthesis_outliner.py --audience ...` and the files in `assets/`.

| Audience | CLI | Lead with | Hide / demote | Assets |
|----------|-----|-----------|---------------|--------|
| Executive | `--audience executive` | Answer, confidence, decision, residual risk | Methods diary | `decision-memo.md` |
| Product / GTM | `--audience product` | Claims safe to make; what to stop saying; watch list | Historiography | `decision-memo.md`, `teardown-canvas.md` |
| Policy / legal | `--audience policy` | Rule vs practice vs guidance; facts that change outcome | Hot takes | `findings-memo.md` |
| Academic | `--audience academic` | Methods, effect sizes, research agenda | Sales language | `findings-memo.md` |
| Investigative | `--audience investigative` | Full layers 1–6 + audit log | Nothing material | all |

## Layer contract (never skip on medium+)

1. **Executive summary** 150–300 words, dated.
2. **Key findings** — claim + locator + confidence tag.
3. **Detailed analysis** — mechanisms, tables, timelines.
4. **Appendix** — annotated bibliography / scored sources.
5. **Limitations & agenda** — gaps, volatility, next queries.
6. **Decision frame** (optional) — options, reverse-the-call evidence.

Light effort may omit 3 and 6 but **not** 1, 2, and 5.

## Voice

Neutral, precise, non-sycophantic. No false certainty. No moralizing on polarized topics. Steelman, then weight.

## Citations

Every non-obvious factual claim needs a locator (URL, DOI, case citation, dataset id). If the host platform has an inline citation component, use it *and* keep the appendix. Bare “Source A” is not an audit trail.

## Confidence tags

Use the ladder from `confidence_calibrator.py`: Very High >90 / High 70–90 / Medium 50–70 / Low <50, with drivers.

## As-of discipline

Controversial, legal, scientific, or market-moving topics open with:

> Evidence assessment as of YYYY-MM-DD. Public discourse, data, or case law may have shifted since.

## Anti-deliverables

- Bullet dump of search snippets
- Smooth essay with no locators
- Balanced-looking 50/50 when the evidence is not
- Recommendations that ignore the user’s actual decision
