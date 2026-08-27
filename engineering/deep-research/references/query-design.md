# Query design (web, academic, code, docs, filings)

`query_expander.py` implements these patterns deterministically. Use it, then *execute* the queries with whatever search tools the host agent has.

## Always emit a set, not a sentence

Minimum set for medium+ depth:

1. Exact-phrase precision
2. Broad recall / synonym OR-group
3. `site:` government pack (geo-aware)
4. `site:` academic pack + `filetype:pdf`
5. Quality news pack
6. **Disconfirming** pack (`"failed to replicate"`, `"we find no evidence"`, critique)
7. Recency (`after:YYYY-MM-DD` or `since:`)

Never run a single clever query and call it a landscape.

## Operators (portable subset)

| Operator | Use |
|----------|-----|
| `"exact phrase"` | Precision; lock operationalizations |
| `OR` / `()` | Synonyms, statutes vs common names |
| `-term` / `-site:` | Drop content farms, job boards, Pinterest |
| `site:` | Domain packs |
| `filetype:pdf\|xlsx\|csv` | Reports and data |
| `intitle:` / `inurl:` | Docs vs marketing pages |
| `after:` / `before:` / `since:` | Recency (syntax varies by engine — emit both) |
| `author:` / `source:` | Scholar-style; harmless if ignored |

Do not invent engine-specific operators the host cannot run. If the tool only takes a string, pass the string.

## Pack recipes

**Government (GLOBAL):** oecd.org, who.int, imf.org, worldbank.org, un.org  
**AU:** abs.gov.au, fairwork.gov.au, fwc.gov.au, legislation.gov.au, pc.gov.au, asic.gov.au  
**US:** census.gov, bls.gov, gao.gov, sec.gov, congress.gov  
**UK:** gov.uk, ons.gov.uk, legislation.gov.uk  
**EU:** europa.eu, eur-lex.europa.eu, eurostat.ec.europa.eu  

**Academic:** arxiv.org, pubmed, jstor, ssrn, nber, `"systematic review"`  
**Filings:** sec.gov 10-K / 8-K, asic.gov.au, companieshouse  
**Code:** github.com, rfc-editor.org, datatracker.ietf.org  
**Patents:** patents.google.com, uspto.gov, espacenet  

## Horizon vs verification

- Horizon: 3–6 **independent** queries in one round (different packs).
- Verification: one claim, one primary, verbatim extract. No new landscape.

## ACI for browse tools

Bad: “summarize this page”.  
Good: “Extract: all quantitative findings with N and window; methods; limitations; funding; author credentials; date; anything that contradicts the claim ‘…’. If paywalled or truncated, say so and stop.”

## Social / X

Useful for primary voices, breaking docs, sentiment. Treat as testimony. Cross-check viral claims against high-integrity sources. Do not use engagement as a quality score.

## Failure recovery

Paywall, empty SERP, tool error → log it on the card (`notes`), switch pack, try `filetype:pdf`, official mirror, DOI, or gazette. Never fabricate the PDF you could not open.
