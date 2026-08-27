# Tool Orchestration Guide

Platform-agnostic patterns for search, extraction, parallelization, and failure recovery during Phases 2-3. Adapt tool names to your environment (web search, browse, MCP connectors, subagents).

---

## Search Strategy

### Query Variation (4-8 queries minimum)

Never rely on a single search. Vary across:

| Variation Type | Example |
|---------------|---------|
| Synonyms | "AI regulation" / "artificial intelligence governance" |
| Boolean | `"EU AI Act" AND "SaaS" NOT "opinion"` |
| Site restriction | `site:.gov "health statistics" 2024` |
| File type | `"annual report" filetype:pdf [company]` |
| Recency | `after:2024-01-01 "topic"` |
| Contrarian | `"topic" criticism OR limitations OR controversy` |
| Academic | `"topic" systematic review OR meta-analysis` |
| Primary docs | `"topic" dataset OR "raw data" OR legislation` |

### Search Round Structure

**Round 1 — Horizon (broad):** 2-3 varied queries → map landscape, identify anchor sources
**Round 2 — Targeted (precision):** Site restrictions, specific entities, primary documents
**Round 3 — Verification (contrarian):** Disconfirming queries, gap-filling, outlier voices

**Stopping criteria:** 70-80% sub-questions have ≥1 relevant source; diminishing returns on new source types.

---

## Extraction Best Practices

### Before Browsing/Extracting

Define laser-focused extraction goal:
- What specific data do you need?
- What format should output take?
- What sections of a long document matter?

### Extraction Request Template

```
Extract from [URL/document]:
1. Verbatim quantitative findings (numbers, percentages, sample sizes)
2. Methodology description (sample, controls, limitations)
3. Funding/conflict disclosures
4. Author credentials and institutional affiliation
5. Publication date and peer-review status
6. Explicit caveats or limitations stated by authors

Do NOT interpret or summarize until extraction is complete.
If paywalled/truncated: note exact error and suggest open alternatives.
```

### PDF / Long Document Handling

- Request section-specific extraction (methods, results, limitations)
- Extract tables as structured data when possible
- Note page numbers for citation traceability

---

## Parallelization Patterns

### Independent Parallel Tasks

Execute simultaneously when logically independent:

```
Parallel batch 1:
├── Search: government sources on [topic]
├── Search: academic literature on [topic]
├── Search: contrarian/criticism on [topic]
└── Search: primary documents/datasets on [topic]
```

### DAG-Style Decomposition

For complex queries, decompose into sub-questions:

```
         [Main Query]
        /    |    \
   [SQ1]  [SQ2]  [SQ3]     ← Parallel retrieval
      \    |    /
    [Synthesis Node]         ← Sequential merge
         |
   [Verification Loop]      ← Sequential validation
```

### Subagent Delegation (when available)

For independent sub-questions, delegate to subagents with focused prompts:

```
Prompt template:
"You are a research subagent. Investigate [specific sub-question].
Use web search and document extraction.
Produce structured summary with:
- Key claims with source citations
- Credibility notes per source
- Evidence gaps
- Recommended follow-up searches
Write findings to [artifact path]."
```

Run multiple subagents in parallel; aggregate summaries in parent session.

---

## Source-Type Search Recipes

### Government / Official

```
site:.gov "[topic]"
site:who.int OR site:oecd.org "[topic]"
"[agency name]" annual report [year]
```

### Academic

```
"[topic]" systematic review
"[topic]" meta-analysis
site:arxiv.org "[topic]" (note: preprint caveats)
site:scholar.google.com "[topic]" (via targeted queries)
```

### Legal / Regulatory

```
"[statute name]" full text
"[regulation]" site:.gov filetype:pdf
"[case name]" court decision
```

### Business / Market

```
"[company]" 10-K OR annual report filetype:pdf
"[company]" site:sec.gov
"[industry]" market size report
```

### News / Current Events

```
"[topic]" investigation site:[reputable outlet]
"[topic]" since:[date] (for recency)
```

### Social / Sentiment (testimony, not fact)

```
"[topic]" expert thread OR analysis
"[topic]" since:[date] (monitoring)
```

Always corroborate social media claims with Tier 1-2 sources.

---

## Failure Recovery

| Failure | Response |
|---------|----------|
| Paywall | Search for open version, author preprint, institutional repository, or secondary summary with primary trace |
| Truncated extraction | Re-request specific sections; try alternative URL (DOI, archive.org) |
| No results | Broaden query; try synonyms; change source type; document sparsity |
| Tool error | Log failure; try alternative tool/path; trigger replan if critical |
| Low diversity | Add site: restrictions for underrepresented source types |
| Conflicting results | Trigger verification loop; classify disagreement type |

**Never:** Fabricate access, invent sources, or treat search snippets as verified facts.

---

## Context Management (Long Sessions)

### Checkpoint Strategy

After each phase, persist:
- Research plan and completed milestones
- Source ledger with credibility scores
- Evidence matrix progress
- Open questions and gaps

### Compaction Survival

Before context limits:
1. Write structured artifacts to files
2. Summarize completed phases (decisions, key findings, confidence)
3. Preserve verification queue and open gaps
4. Re-read plan artifact after compaction

---

## ACI (Agent-Computer Interface) Principles

Apply to every tool instruction:

1. **Precise parameters** — Specific queries, URLs, extraction targets
2. **Example-rich** — Show desired output format
3. **Edge-case aware** — "If no results, state explicitly and suggest alternatives"
4. **Mistake-proofed** — Clear boundaries; avoid ambiguous instructions
5. **Natural formats** — Request structured output (JSON, tables) when useful

### Bad vs Good Tool Instructions

**Bad:** "Search for information about AI regulation"

**Good:** "Search for 'EU AI Act compliance requirements SaaS companies 2025'. Return top 15 results. For each: title, URL, date, source type (government/academic/news). Prioritize .eu and .gov domains."

---

## Integration with Repo Skills

| Need | Skill | Handoff Point |
|------|-------|---------------|
| Web source discovery | `seo-audit`, `ai-seo` | Phase 2 horizon scanning |
| Competitive data | `competitive-teardown` | Business/market research |
| Data analysis | `financial-analyst`, `senior-data-scientist` | Phase 5 quantitative validation |
| Regulatory research | Domain compliance skills | Phase 3-4 domain-specific acquisition |
| Report formatting | Document skills | Phase 6 output packaging |

Document handoffs in research log. This skill remains self-contained — cross-skill use is optional enhancement.

---

## BYOK Patterns (Optional)

Some environments support API-enhanced search. Document any BYOK usage:

| Service | Use Case | Fallback |
|---------|----------|----------|
| Semantic Scholar API | Academic paper metadata | Standard web search + site: restrictions |
| CrossRef API | DOI resolution | Manual DOI lookup |
| News API | Current events monitoring | Web search with recency filters |

All scripts in this skill use stdlib only. BYOK is agent-level enhancement, not script dependency.
