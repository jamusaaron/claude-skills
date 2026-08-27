# Citation Standards (traceable research outputs)

Every non-obvious claim in a deep-research deliverable must be independently retrievable. Style can vary; **traceability cannot**.

## Minimum viable citation

For each factual claim, record:

| Field | Why |
|-------|-----|
| Stable ID | Source ledger id (`s_oecd_remote`) |
| Title | Human retrieval |
| Author / org | Provenance |
| Date (YYYY-MM-DD or year) | Vintage |
| Locator | URL, DOI, statute section, page/para |
| Retrieved | Date you fetched it |
| Integrity band | From the 12-point rubric |
| Claim excerpt | What exactly it supports |

Inline form (deliverable):

> Remote-first cycle time shows a small negative pooled effect (Chen & Okonkwo 2025, High; meta-analysis of 31 studies).

Do not use a bare URL as the only citation for a pivotal fact.

## Locator preference (strongest first)

1. Statute / regulation section; case citation; official statistical table id
2. DOI or Handle
3. Canonical publisher URL
4. Archived URL (archive.org) if the live page is volatile
5. Report edition + page
6. Timestamped social post URL (testimony only)

## Independence in citation lists

Citing six news stories that all reprint the same embargo is **one** source. In the bibliography, list the primary and optionally note "widely reprinted."

The annotated bibliography (`scripts/output_packager.py --kind bibliography`) should include contribution + limitations columns so a skeptic can audit without reopening every link.

## Quote vs paraphrase

- Numbers, legal tests, and definitions: quote or extract exactly, then interpret.
- Long-form argument: paraphrase and cite.
- Never stitch a quote that changes meaning (ellipsis abuse).

## User-supplied documents

Cite as: *Author, Title, date, user-supplied, sha256 or filename, page.* Do not pretend they are public.

## Controversial / volatile topics

Lead with: **Evidence assessment as of [date].** If the claim is in active litigation or a fast-moving outbreak, say so in Layer 1.

## What not to do

- "According to experts" (name them)
- "Recent studies" (count, design, year)
- Footnote farms that do not map to claims
- Mixing a High source and a Low source in one superscript as if they were peers
- Citation to a tool snippet you did not open

## Mapping to scripts

- Ledger → `assets/source-tracker-template.csv` or notes JSON `sources[]`
- Graph → `scripts/citation_graph.py` (`cites` edges)
- Packaged biblio → `scripts/output_packager.py --kind bibliography`
