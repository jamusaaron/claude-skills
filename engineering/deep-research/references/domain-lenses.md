# Domain lenses (optional packs)

Load **one** pack when Phase 0 detects a domain (or when `research_planner.py` prints it). Lenses add questions and source priors. They do not replace Phases 0–10 and they do not make this skill a licensed professional.

Default personality of this skill: **global, jurisdiction-agnostic, non-partisan methodology**. Regional law is opt-in.

## Scientific

**Add to Phase 1:** operational outcome, population, estimand (ITT vs per-protocol), minimum effect that would matter.

**Prefer:** peer-reviewed reports, registered protocols, replication packages, systematic reviews.

**Distrust:** press-office relative-risk headlines; p-hacking tells (many uncorrected outcomes); "first-ever" without a search.

**Extra criticism:** identification, multiple comparisons, researcher degrees of freedom, data leakage (especially ML).

**Output:** effect sizes with uncertainty; replication status; what a methods critic would try first.

## Legal and policy (generic)

This is **research about law and policy**, not legal advice.

**Distinguish always:**

1. Black-letter text (statute, regulation, judgment)
2. Official guidance (persuasive, not always binding)
3. Enforcement / tribunal *practice*
4. Commentary (academic, media, advocacy)

**Phase 1 extras:** jurisdiction, forum, date of force, what question is legal vs political vs empirical.

**Prefer:** official gazettes, court databases, bills + explanatory notes, Hansard / congressional record, regulator registers.

**Distrust:** social-media case summaries; undated blogs; mixing one country's doctrine into another.

**Output:** "As of {date} in {jurisdiction}, the operative instrument says … Practice in {forum} appears … Commentary claims … Confidence separately for each layer."

### Optional pack: Australian / Commonwealth legal-policy

Use **only** if the user asks, or the facts are clearly AU/UK-Commonwealth.

- Map **federal vs state/territory** (or UK reserved/devolved) before quoting a statute.
- Prefer: legislation.gov.au / legislation.gov.uk, AustLII / BAILII, national statistics offices, parliamentary libraries, Fair Work / ACAS-type industrial bodies when employment is in scope.
- Employment examples (illustrative, not a playbook for a specific person): general protections vs unfair dismissal are different actions; reverse onus and protected attributes are *jurisdiction-specific* — cite the section, do not analogize silently from another country.
- Superannuation, tribunals (e.g. VCAT-class state tribunals), and ombudsmen are **separate forums**; do not collapse them.
- Indigenous law, native title, and closing-the-gap reporting require that lens explicitly — do not token-add a paragraph.
- If the user is a party to a live dispute: this skill still only does public-source research; it does not replace a solicitor.

## Market and competitive

**Prefer:** filings, audited accounts, pricing pages (archive them), independent usage panels, job posts as *capability signals*.

**Distrust:** TAM slides, "N of 1" customer quotes in vendor decks, SEO blogs citing each other.

**Extra:** unit economics vs vanity metrics; cohort vs blended; one-off vs run-rate.

Overlap with competitive-teardown / competitive-intel skills is optional; this pack still works standalone.

## Geopolitical

**Prefer:** primary official texts, treaty deposits, conflict datasets (ACLED, UCDP), trade/customs, local-language reporting.

**Distrust:** map memes; unnamed "intelligence sources" in a single outlet; moral frames posing as order-of-battle.

**Extra:** time zones of events; propaganda from all states including ones you like; humanitarian vs military vs legal characterizations as *separate claims*.

## Medical and public health (non-diagnostic)

**Hard stop:** no diagnosis, no dosing, no "you should take". Research population-level evidence only.

**Prefer:** Cochrane/WHO/CDC/NICE-class reviews, regulator labels, large RCTs, registries.

**Require:** absolute risks, population, comparator, harm signals.

**Distrust:** supplement marketing; single observational papers on diet/lifestyle causal claims; subgroup fishing.

If the user asks "do I have X" or "what should I take": refuse the clinical act; offer general published evidence *about a condition* only if they still want that, with a clinician pointer.

## Technical due diligence

**Prefer:** specs, RFCs, source, CVEs/NVD, independent benchmarks, postmortems, architecture decision records.

**Distrust:** vendor "up to" performance; unaudited AI eval leaderboards; security claims without scope.

**Extra:** threat model; what was *not* tested; operational toil; lock-in.

## How to attach a lens

In the plan: `domain: legal` + `jurisdiction_pack: AU` (optional). Load this file's matching section only. Do not load all packs.
