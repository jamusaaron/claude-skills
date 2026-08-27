# OSINT-Safe Practices (research, not intrusion)

This skill is for **open-source research**: published pages, public records, consented interviews, user-supplied documents. It is not a hacking, social-engineering, or surveillance playbook.

## Allowed collection

- Public web search and page fetch
- Public government gazettes, court databases, company registers, statistical agencies
- Academic indexes and preprints
- Public social posts treated as **speech/testimony**, not as identity dossiers
- Documents the user already has rights to share

## Hard stops

Do not:

- Bypass paywalls, logins, access controls, or CAPTCHAs
- Request or handle passwords, session tokens, or MFA codes
- Scrape in violation of robots/ToS when a reasonable public excerpt would do
- Dox, stalk, or compile non-public personal data about private individuals
- Use leaked databases of personal information as evidence without a clear public-interest *and* legality path — default is **do not**
- Impersonate, pretext, or phish for documents
- Probe systems "to see if they're public"

If a source is only available via unauthorized access, write: "Primary not legally reachable; conclusion bounded."

## Handling people

- Private individuals: minimize. Quote public figures on public statements.
- Vulnerable groups: trauma-informed framing; no unnecessary case detail.
- Employees leaking internal docs: corroborate, do not amplify identity.
- Interviews: consent, purpose limitation, store separately from the public bibliography if needed.

Use `assets/interview-protocol-template.md` for human sources.

## Operational security for the researcher

- Prefer official URLs over shortened/random domains
- Do not open mystery binaries or macros to "extract the data"
- Record retrieval date; pages change
- Hash or note version of user-supplied files
- Separate *working notes* (may contain PII) from *deliverable* (should not)

## Social and viral sources

X/Twitter, Reddit, TikTok, YouTube comments:

- Good for: primary speech, emerging terms, eyewitness *leads*
- Bad for: prevalence, causation, "everyone thinks"
- Always note amplification (views, brigading, bot-like repetition)
- Corroborate any factual claim downstream

## Jurisdiction and records

- FOI/public-records requests: legal in many places; still not a hack. Cite the request id if used.
- Court documents: check publication rules (suppression, minors).
- Health and education records: default confidential.

## Attribution without harm

Cite so a reader can find the artifact. If quoting a non-public person who did not consent to amplification, paraphrase and withhold identifiers unless the user is that person or has a lawful brief.

## When to stop and say so

Information-scarce, classified, or proprietary domains: state sparsity, give first-principles bounds, and recommend a lawful primary collection step (FOI, expert retainer, user data pull). Do not invent access.
