# Research playbooks (competitive, market, technical, academic, legal)

Load the playbook that matches `--mode` from `research_planner.py`. Combine packs; do not pretend one literature is the whole world.

## Academic / scientific

**Anchors:** systematic reviews, preregistered RCTs, official stats, replication attempts, COI statements.

**Queries:** `"systematic review"`, `"meta-analysis"`, `filetype:pdf`, `site:nih.gov`, `site:arxiv.org`, negative results (`"we find no evidence"`).

**Gotchas:** p-hacking, outcome switching, preprint ≠ peer review, effect size vs significance, generalizability.

**Output:** methods layer + uncertainty ladder + “what a decisive experiment looks like”.

## Market / competitive

**Anchors:** filings (10-K, annual reports), pricing pages (dated snapshot), win/loss notes, changelog, hiring, review-site *patterns* (not single quotes).

**Queries:** `site:sec.gov`, `"10-K"`, job boards + role families, Ad Library, G2/Capterra *themes*.

**Gotchas:** vendor TAM slides, circular analyst citations, review bombing, list price ≠ net price.

**Output:** product/GTM outline — claims safe to make, claims to stop, watch items.

Companion (optional, not a hard dep): competitive-intel, competitive-teardown.

## Technical / engineering

**Anchors:** spec + implementation, independent benchmarks *with methodology*, CVEs, postmortems, RFCs.

**Queries:** `site:github.com`, `site:rfc-editor.org`, `filetype:pdf` architecture, CVE ids.

**Gotchas:** vendor benches, demo-ware, “10x” without workload, security claims without threat model.

**Output:** decision frame: migrate / wait / reject, with lock-in and ops burden.

## Legal / regulatory / policy

**Split every finding into:** black-letter rule | tribunal/court practice | regulator guidance | advocacy.

**AU example hosts:** legislation.gov.au, austlii.edu.au, fwc.gov.au, fairwork.gov.au, abs.gov.au, pc.gov.au.

**US/EU/UK:** see `query_expander.py` `--geo` packs.

**Gotchas:** quoting a fact sheet as if it were the statute; ignoring onus, standing, limitation periods, federal vs state; treating one first-instance decision as settled law.

**Output:** policy/legal outline with “facts that would change the outcome”.

## Historical

**Anchors:** contemporaneous documents, archives, competing historiographies.

**Gotchas:** presentism, single-archive bias, later memoirs treated as contemporaneous.

## Journalism-heavy topics

Start at wire services and investigations that publish documents. Use news to *find* primaries, then cite the primary. Viral social is testimony.

## Information-scarce / emerging

Lead with sparsity. Use labeled analogs and mechanical bounds. Recommend FOI, archive, or expert interview protocol (`assets/interview-protocol.md`).
