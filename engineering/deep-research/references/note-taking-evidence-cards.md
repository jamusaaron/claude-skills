# Structured note-taking: evidence cards and Zettelkasten

The evidence store is the research memory. If it is not in the store, it does not exist at synthesis time.

## Evidence card (canonical)

```json
{
  "id": "ev-...",
  "url": "https://...",
  "doi": "10.xxxx/...",
  "title": "",
  "authors": [],
  "published": "YYYY-MM-DD",
  "retrieved": "YYYY-MM-DDThh:mm:ssZ",
  "source_type": "government|academic|primary|news|...",
  "question_id": "Q1",
  "claims": [
    {"id": "c-...", "text": "Falsifiable sentence.", "polarity": "supports|refutes|neutral", "question_id": "Q1"}
  ],
  "quotes": ["Verbatim, with enough context to survive a challenge."],
  "credibility": {"score": 0, "band": "high", "notes": ""},
  "tags": ["method:rct", "geo:AU"],
  "persona": "analyst",
  "notes": "Limitations, funding, what you did *not* extract."
}
```

CLI: `python scripts/evidence_store.py add --store research.jsonl ...`

## Atomicity

- One **claim** = one falsifiable proposition. Not a paragraph.
- Quotes are not claims. Promote a quote to a claim only after you state it in your own operationalized language.
- If a source supports Q1 and refutes Q3, that is two claims, two polarities.

## Zettelkasten mapping

| Zettel type | Store equivalent |
|-------------|------------------|
| Literature note | Evidence card (source-bound) |
| Permanent note | Clustered claim in `claim_matrix.py` (your words) |
| Structure note | Synthesis outline section |
| Index | Coverage report + question ids |

Never let literature notes masquerade as permanent notes. “Bloom 2022 says…” is a card. “Compressed-week productivity claims fail when output measures replace self-reports” is a finding.

## Extraction discipline (browse / PDF)

When fetching a page, instruct the tool like an ACI:

1. Verbatim quantitative findings (with N, window, operationalization)
2. Methods / sample / limitations / funding
3. Author and institutional identity
4. Publication date and version (preprint vs journal)
5. What the source *explicitly does not claim*

Summarize only after extraction. Do not interpret in the same pass.

## IDs and resume

- Stable `id` values (`ev-iceland-gov`) survive merges.
- Dedup keys: id, DOI, normalized URL, content hash.
- Continuing research: `evidence_store.py merge --store current.jsonl --incoming new.json`

## Minimum viable log for a light pass

If the user wants speed, still keep:

- source locator (URL/DOI)
- one-sentence claim
- band (even if provisional)
- question id

That is enough to run matrix + coverage + calibrator later.
