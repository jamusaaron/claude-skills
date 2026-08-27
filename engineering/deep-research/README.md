# Deep Research

POWERFUL-tier research skill: multi-phase evidence pipelines, source criticism, claim–evidence matrices, contradiction detection, confidence calibration, and resume-able evidence stores.

**Tier:** POWERFUL  
**Category:** Engineering / Knowledge Operations  
**Dependencies:** Python 3.9+ standard library only

## What this is

A self-contained package you can extract into Claude Code, Codex, Gemini CLI, or OpenClaw. It turns “please look into X” into a falsifiable plan, a scored evidence store, and layered deliverables a skeptic can audit.

Not a search API. Scripts do not call the network or LLMs.

## Layout

```
deep-research/
├── SKILL.md
├── README.md
├── scripts/          # 10 CLI tools
├── references/       # methodology, rubrics, playbooks
├── assets/           # templates + sample store
└── expected_outputs/ # golden samples from the CLIs
```

## Quick start

```bash
cd engineering/deep-research

python3 scripts/research_planner.py \
  --topic "Do four-day weeks improve software delivery without harming quality?" \
  --effort medium --format json -o /tmp/plan.json

python3 scripts/query_expander.py \
  --query "four-day work week productivity RCT" --geo GLOBAL

python3 scripts/evidence_store.py init --output /tmp/store.jsonl
python3 scripts/evidence_store.py merge \
  --store /tmp/store.jsonl \
  --incoming assets/sample_evidence_store.json

python3 scripts/source_scorer.py --input assets/sample_evidence_store.json
python3 scripts/claim_matrix.py --input assets/sample_evidence_store.json
python3 scripts/contradiction_detector.py --input assets/sample_notes.jsonl
python3 scripts/coverage_analyzer.py --plan /tmp/plan.json --store assets/sample_evidence_store.json
python3 scripts/confidence_calibrator.py --input assets/sample_evidence_store.json
python3 scripts/citation_normalizer.py --input assets/sample_evidence_store.json --style apa
python3 scripts/synthesis_outliner.py --plan /tmp/plan.json --audience executive
```

Every script supports `--help` and `--format json`.

## Scripts

| Script | Purpose |
|--------|---------|
| `research_planner.py` | Question decomposition, hypotheses, pre-mortem, DAG |
| `query_expander.py` | Boolean / site: / filetype: / scholarly variants |
| `evidence_store.py` | init / add / merge / query / stats / export |
| `source_scorer.py` | 12-dimension credibility + recency |
| `claim_matrix.py` | Claim clusters and independence |
| `contradiction_detector.py` | Numeric, negation, antonym clashes |
| `coverage_analyzer.py` | Gaps vs declared questions |
| `citation_normalizer.py` | APA, BibTeX, CSL-ish |
| `synthesis_outliner.py` | Stakeholder-shaped outline |
| `confidence_calibrator.py` | Uncertainty ladder |

## Workflow (short)

1. Brief (`assets/research-brief.md`) → planner  
2. Expander → search/fetch into the store  
3. Score, matrix, contradictions, coverage  
4. Outline + calibrator → findings / decision memo  
5. Skeptic pass → deliver with as-of date  

Full doctrine: `SKILL.md`. Rubric: `references/source-evaluation-framework.md`.

## Quality bar

Pivotal claims need two independent high/medium-integrity sources or one primary. Low-integrity sources stay illustrative. Contested findings stay in the main findings, not the basement.

## License

MIT, same as the parent library.
