# Search query playbook

Load this in **Phase 2**. Generate the set with `scripts/search_query_generator.py`, then *execute* it. A taxonomy that stays in the plan is not a horizon scan.

## Families (run all nine on standard+)

| Family | Purpose | Stop condition |
|--------|---------|----------------|
| `direct` | Canonical phrasing of the restated query | First useful primary leads |
| `synonym` | Controlled vocabulary the user did not type | New venues, not new adjectives |
| `contradiction` | Criticism, failure, vs, confounders | At least one disconfirming lead or a logged null |
| `site_academic` | Papers, preprints, university pages | 2–3 method-bearing hits |
| `site_gov` | Official stats, legislation, regulators | 1–2 primaries or a logged absence |
| `filetype_pdf` | Reports, judgments, methods notes | Open the PDF; snippets lie |
| `recency` | `after:YYYY-01-01`, year tokens | Confirms the window |
| `stakeholder` | Named camps | At least two opposing camps represented |
| `dataset` | Microdata, registries, filings | A locator or a logged absence |

Optional tenth: `multilingual` when the phenomenon is not primarily Anglophone.

## Operators (portable)

These work in most web search tools. If a platform lacks an operator, emulate with extra keywords.

```
"exact phrase"
OR / |
-exclude
site:.gov  site:.gov.au  site:arxiv.org  site:europa.eu
filetype:pdf
after:2024-01-01     (Google-style; else add the year)
intitle:methodology
```

Scholarly hunting when you have no Scholar API:

- `"{topic}" site:arxiv.org`
- `"{topic}" site:pubmed.ncbi.nlm.nih.gov`
- `"{topic}" "supplementary materials" OR "replication package" OR OSF`
- DOI hunting: paste the DOI into a fetch tool, not only the news write-up

Government / IGO:

- National stats offices, gazettes, legislatures, regulators
- Jurisdiction packs (script `--jurisdiction AU|UK|US|EU|CA|NZ|IN|SG`) **add** local domains; they do not replace global ones

Datasets:

- `filetype:csv "{topic}"`
- Named systems: clinicaltrials.gov, SEC EDGAR, ACLED, UCDP, OECD.Stat, national open-data portals

## Query design rules

1. **One family, one intent.** Do not smash contradiction into the first direct query "just in case". You will miss it when the first page looks tidy.
2. **3–6 parallel calls** per round if the platform allows independent tool calls.
3. **Read past the first page** or increase `num_results` where the tool supports it.
4. **Snippets are not evidence.** Promote a hit to Phase 3 only with a fetch/extract instruction.
5. **Log nulls.** "No .gov hits for query Q on date D" is a finding about publicity, not about truth.

## Recency vs foundation

- Decision about *current* law, price, outbreak, CVE: recency family is mandatory.
- Decision about *mechanism* (does this class of drug work via X): mix landmark papers with post-2018 updates.
- Always stamp **as-of** on the scan itself.

## Social / primary testimony (optional adapter)

If the platform has X/Twitter, Reddit, or similar:

- Use for **primary voices**, timestamps, and document leaks — not for prevalence.
- Require `min_faves` / score filters only as a *signal* filter; popularity ≠ truth.
- Cross-check viral tables against the originating PDF.

If the platform has no social search, skip without guilt. Do not fake it.

## Multilingual

When local-language sources matter:

1. Search the local terms (do not rely on English calques).
2. Prefer official bilingual pages and certified translations for legal text.
3. Note translation risk on any claim that depends on a nuance ("shall" vs "may").
4. Never use a black-box translate of a judgment as the last word.

## Horizon-scan coverage test

After 2–3 tool rounds you should be able to fill:

- Glossary of contested terms
- Timeline of major instruments / papers
- Stakeholder map (names, not archetypes only)
- Anchor list (3–7 High/Medium-High leads)
- Outlier list (contrarian but methods-bearing)

If 70%+ of hits are news explainers, you have not scanned; you have aggregated. Replan toward `site:` and `filetype:pdf`.

## Replan triggers from search

See Phase 1 plan. Search-specific:

- Entire first page is syndication of one press release → add `-site:` of that publisher and hunt the primary.
- All academic hits are the same lab → add replication / "failed to replicate" queries.
- Government hits 404 or embargoed → note and use explanatory memoranda / FOI logs.
