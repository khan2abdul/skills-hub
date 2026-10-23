---
name: check-my-security
description: Threat-model-driven security review of a change, feature, or subsystem: a STRIDE pass over the actual code, an OWASP cross-check, severity x exploitability triage, and a filing-ready report with a concrete exploit and remediation per finding. Use before shipping anything that touches auth, input handling, secrets, or data storage.
---

# Check My Security

Composed from verbatim excerpts of 9 upstream skills. Each section is
byte-identical to its source; provenance and hashes are in PROVENANCE.md.
Do not paraphrase a section when editing - change the compose spec instead.

<!-- source: security-and-hardening | ## Process: Threat Model First | sha256: a5c8e5a466cabf28f2e79dc8fd6e72a07cb8961d20b124fcd18031c56f59f907 -->

## Process: Threat Model First

Controls bolted on without a threat model are guesses. Before hardening, spend five minutes thinking like an attacker:

1. **Map the trust boundaries.** Where does untrusted data cross into your system? HTTP requests, form fields, file uploads, webhooks, third-party APIs, message queues, and **LLM output** — plus the local values that look internal because the OS handed them to you: another process's command line or environment, filenames on a shared volume, a path in a job payload. Trust follows who *wrote* a value, not which channel delivered it. Every boundary is attack surface.
2. **Name the assets.** What's worth stealing or breaking? Credentials, PII, payment data, admin actions, money movement.
3. **Run STRIDE over each boundary** — a quick lens, not a ceremony:

| Threat | Ask | Typical mitigation |
|---|---|---|
| **S**poofing | Can someone impersonate a user/service? | Authentication, signature verification |
| **T**ampering | Can data be altered in transit or at rest? | Integrity checks, parameterized queries, HTTPS |
| **R**epudiation | Can an action be denied later? | Audit logging of security events |
| **I**nformation disclosure | Can data leak? | Encryption, field allowlists, generic errors |
| **D**enial of service | Can it be overwhelmed? | Rate limiting, input size caps, timeouts |
| **E**levation of privilege | Can a user gain rights they shouldn't? | Authorization checks, least privilege |

4. **Write abuse cases next to use cases.** For each feature, ask "how would I misuse this?" — then make that your first test.

If you can't name the trust boundaries for a feature, you're not ready to secure it. This is OWASP **A04: Insecure Design** — most breaches begin in design, not code.

<!-- source: security-and-hardening | ## The Three-Tier Boundary System | sha256: 01be026c89cf28e52fcec1d1de266df6cbce2874e1e4c012845a6a06ca9e0412 -->

## The Three-Tier Boundary System

### Always Do (No Exceptions)

- **Validate all external input** at the system boundary (API routes, form handlers)
- **Parameterize all database queries** — never concatenate user input into SQL
- **Encode output** to prevent XSS (use framework auto-escaping, don't bypass it)
- **Use HTTPS** for all external communication
- **Hash passwords** with bcrypt/scrypt/argon2 (never store plaintext)
- **Set security headers** (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- **Use httpOnly, secure, sameSite cookies** for sessions
- **Run the detected package manager's native audit** against the committed lockfile before every release

### Ask First (Requires Human Approval)

- Adding new authentication flows or changing auth logic
- Storing new categories of sensitive data (PII, payment info)
- Adding new external service integrations
- Changing CORS configuration
- Adding file upload handlers
- Modifying rate limiting or throttling
- Granting elevated permissions or roles

### Never Do

- **Never commit secrets** to version control (API keys, passwords, tokens)
- **Never log sensitive data** (passwords, tokens, full credit card numbers)
- **Never trust client-side validation** as a security boundary
- **Never disable security headers** for convenience
- **Never use `eval()` or `innerHTML`** with user-provided data
- **Never store sessions in client-accessible storage** (localStorage for auth tokens)
- **Never expose stack traces** or internal error details to users

<!-- source: security-and-hardening | ## Hardening Controls | sha256: 97dd7b47e6e48087d8ffa8f6b9e4bf0b0fd95c1cde0dd8ad8b9732cfdb7d9990 -->

## Hardening Controls

The rules below are the workflow; a concrete implementation of each lives in [references/hardening-patterns.md](references/hardening-patterns.md). Open the section you need when you reach that code, not before.

### Injection, XSS, and access control

- Parameterize every query. Never build SQL, NoSQL, or shell commands from input strings.
- Encode output through the framework's auto-escaping. If raw HTML is unavoidable, sanitize with an allowlist sanitizer first.
- Check **authorization** on every request, not just authentication: the authenticated user must own, or be permitted on, the specific resource (A01, IDOR).

Patterns: [Injection](references/hardening-patterns.md#injection), [XSS](references/hardening-patterns.md#cross-site-scripting-xss), [Access control](references/hardening-patterns.md#broken-access-control).

### Authentication and sessions

- Hash passwords with bcrypt (≥12 rounds), scrypt, or argon2. The session secret comes from the environment, never from code.
- Session cookies are `httpOnly`, `secure`, and `sameSite: 'lax'` or `'strict'` (the CSRF defense; `'none'` sends the cookie on cross-site requests), with a bounded `maxAge`.

Pattern: [Authentication](references/hardening-patterns.md#broken-authentication).

### Headers, CORS, and responses

- Security headers on every response (helmet or the framework equivalent); CSP starts from `default-src 'self'` and is tightened, not loosened.
- CORS restricted to an explicit origin list from configuration. Never `*` with credentials.
- Strip sensitive fields (`passwordHash`, reset tokens) before any response. Error bodies are generic; internals go to server logs only.

Patterns: [Misconfiguration](references/hardening-patterns.md#security-misconfiguration), [Sensitive data exposure](references/hardening-patterns.md#sensitive-data-exposure).

### Input validation and uploads

- Validate at the boundary with a schema: allowlisted shape, lengths, enums, formats. Reject with 422 and structured details; downstream code uses only the parsed, typed value.
- Uploads: allowlist MIME types, cap size, verify content (magic bytes) when it matters. The extension proves nothing.

Patterns: [Schema validation](references/hardening-patterns.md#schema-validation-at-boundaries), [File upload](references/hardening-patterns.md#file-upload-safety).

### Server-side fetches (SSRF)

Any URL the user influences — webhooks, import-from-URL, image proxies, link previews — can be aimed at internal services. Allowlist scheme and host, resolve **all** DNS records and reject any private or reserved address (loopback, link-local `169.254.169.254`, private, unique-local, for IPv4 and IPv6), and forbid redirects. That check still has a DNS-rebinding TOCTOU gap: for high-risk surfaces, pin the resolved IP or put a filtering agent in front.

Pattern: [SSRF](references/hardening-patterns.md#server-side-request-forgery-ssrf).

### Destructive operations on derived paths

A delete, move, or overwrite is only as safe as the value naming its target, and trust follows who *wrote* that value, not which channel delivered it: another process's command line is as attacker-controlled as a form field. A shape check proves well-formedness, not authorization. Before the call, require all three: the resolved target (symlinks resolved) sits under an **allowlisted root**; it is at least one level **below** that root; and it carries **ownership evidence read before the operation**. On refusal, log the rejected target and stop; never fall back to a broader default path.

Why the check is weaker than it reads (marker self-attestation, check/use races): [Destructive paths](references/hardening-patterns.md#destructive-operations-on-derived-paths). Worked code: `../../references/security-checklist.md`.

### Rate limiting

Limit the API generally and auth endpoints strictly (about 10 attempts per 15 minutes). Once more than one process serves traffic, in-memory counters silently become `max × instances`, or never fire on serverless: back the limiter with a shared store.

Pattern: [Rate limiting](references/hardening-patterns.md#rate-limiting).

### Secrets

Secrets come from the environment. `.env.example` is committed with placeholders; real `.env*` files and key material are gitignored; grep the staged diff before committing. **A secret that reaches a remote is compromised the moment it lands: rotate it first, then purge history.**

Pattern: [Secrets management](references/hardening-patterns.md#secrets-management).

### Dependencies and supply chain

1. **Find the installation boundary and manager.** Use the workspace root that owns the lockfile, or an independent nested project only when it is outside that workspace. Corroborate `packageManager` (when present), the lockfile, and CI; stop on disagreement or competing lockfiles. Pin the manager version.
2. **Block dependency scripts before first execution.** Bootstrap with scripts disabled or a documented fail-closed policy, inspect the pending script source, approve only the minimum, commit the policy, then verify with a clean frozen/immutable install. Never blanket-approve.
3. **Run the native audit against the committed lockfile before every release.** Triage critical/high by **reachability** (runtime, build, test, deploy paths) and fix availability. Never apply forced remediation (`npm audit fix --force` or equivalent) automatically, since forced fixes may cross declared dependency ranges; preview, read changelogs, test each upgrade. Document every deferral with a reason and a review date.
4. **Audits only match known advisories.** They do not catch a newly malicious or typosquatted package (`cross-env` vs `crossenv`). Review new dependencies, lockfile diffs, and script-policy changes together: ownership, maintenance, release age, provenance, transitive graph. Verify registry signatures where supported (`npm audit signatures`, `pnpm audit signatures`) and treat their absence as a signal to investigate, not automatic proof of compromise (A06, LLM03).

Triage decision tree: [Dependency audit triage](references/hardening-patterns.md#dependency-audit-triage). Manager matrix and install-script gate: `../../references/security-checklist.md`.

### Personal data and privacy

Hardening asks "can an attacker read it?" Privacy asks "should *we* hold it at all, and for how long?" The cheapest data to protect, breach, and comply over is the data you never collected; treat personal data as a liability to minimize.

- **Classify fields as you add them** (non-personal, PII, sensitive) and handle each class accordingly. You cannot protect, or honor a deletion request for, data you cannot find.
- **Collect only against a stated purpose.** "Might be useful later" is latent breach scope, not a purpose. Keep PII out of telemetry (the `observability-and-instrumentation` skill makes the same point from the ops side).
- **Set retention up front, then actually delete.** Every personal-data store needs a TTL and a working deletion path, including backups, caches, search indexes, and analytics copies.
- **Support the data-subject rights your jurisdiction requires** (GDPR, CCPA, and kin): export, correct, delete. Design the schema so a user's data is findable and erasable, not smeared irreversibly across systems.
- **Consent gates collection and third-party sharing, and is auditable.** Sending PII to an analytics, ad, or LLM vendor is sharing; the vendor needs a data-processing agreement. Make region a configurable policy, not a hardcoded assumption.

Classification table: [Data classification](references/hardening-patterns.md#data-classification). A privacy incident starts the breach-notification clock; run the postmortem with the `debugging-and-error-recovery` skill.

### AI / LLM features

Calling an LLM — chatbots, summarizers, agents, RAG — adds a new attack surface; map it to the [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/):

- **Model output is untrusted input** (LLM05). Never into `eval`, SQL, a shell, `innerHTML`, or a file path; parse defensively, validate against a schema, then encode.
- **Prompts can be hijacked** (LLM01). Untrusted text in the context — a user message, a fetched page, a PDF — can carry instructions. The system prompt is not a security boundary; enforce permissions in code.
- **Keep secrets, other tenants' data, and the full system prompt out of the context window** (LLM02, LLM07); scope tool permissions, validate every tool argument, and confirm destructive actions (LLM06); cap tokens, request rate, and recursion depth (LLM10); partition RAG embeddings per tenant and validate documents before indexing (LLM08).

Pattern: [LLM output handling](references/hardening-patterns.md#llm-output-handling).

<!-- source: security-review | ## Step 3: STRIDE pass | sha256: a3b453d64f2afc2a827e466987c956716bd3ed920ce9d251290d0719a16fae57 -->

## Step 3: STRIDE pass

For each attack surface, walk STRIDE:

### Spoofing (identity)
- Can an attacker pretend to be another user?
- Are identity tokens verified before they're trusted?
- Session cookies: HttpOnly, Secure, SameSite set?

### Tampering (integrity)
- Can an attacker modify data in transit or at rest?
- Are webhooks signed and signatures verified?
- Are incoming payloads rehydrated without integrity checks?

### Repudiation (audit trail)
- Is there a log of who did what?
- Can an attacker erase their trail?
- Are logs tamper-evident where it matters?

### Information disclosure
- Does an error message leak internal state, stack traces, file paths, DB queries?
- Are secrets logged anywhere?
- Are authorization checks upstream of data loading, or does the query run first?

### Denial of service
- Are there unbounded loops, unpaginated queries, or user-controlled recursion?
- Rate limits on expensive endpoints?
- Regex-on-user-input vulnerable to ReDoS?

### Elevation of privilege
- Are admin-only routes actually gated?
- Can a low-privilege user trigger a high-privilege operation through an unauthenticated webhook?
- Are role checks enforced at the handler, the service, and the data layer — or just one?

Use `Agent(subagent_type=Explore)` in parallel if the scope is large — one sub-agent per STRIDE category over the same surface list.

<!-- source: security-and-hardening | ## Review Checklist | sha256: e5e82f847c0493cda0f5922a34563fb12cecda45b2528dff2234d7e988442440 -->

## Review Checklist

Before sign-off, walk `../../references/security-checklist.md`: it covers authentication, authorization, input, data protection and privacy, headers and CORS, dependencies and supply chain, AI/LLM, and error handling, plus the OWASP quick-reference tables.

<!-- source: security-review | ## Step 5: Triage | sha256: 79283b0dad7df1ffbaa14abb2a33f73a239f464f4ed08e18cdc5e0b1ae205179 -->

## Step 5: Triage

For each finding, assign:

- **Severity:** Critical / High / Medium / Low / Informational
- **Exploitability:** Remote unauthenticated / authenticated user / adjacent user / admin-only / local-only
- **Business impact:** Data breach / account takeover / service disruption / audit failure / minor

Severity × Exploitability = priority. Sort findings by priority.

<!-- source: security-review | ## Step 6: Write the report | sha256: 0a73dad61138e8294e14eda7f85ea86aa5b292bb20d1edbb5bb8af4eab56856f -->

## Step 6: Write the report

```markdown
## Security Review — <scope>

### Summary

<1–3 sentences — biggest finding and overall posture>

### Findings

#### CRITICAL-1: SQL injection in `getUser`

**Location:** `src/db/users.ts:42`
**Category:** Tampering / Info disclosure (STRIDE) + OWASP A03 Injection
**Exploit:** Passing `' OR 1=1--` to the `name` parameter produces the query `SELECT * FROM users WHERE name='' OR 1=1--'`, returning every row. `name` arrives from `POST /api/search` without validation.
**Reachability:** Remote unauthenticated (endpoint has no auth).
**Remediation:** Use a parameterized query. The codebase's `db.prepare` helper at `src/db/util.ts:17` handles this — switch `getUser` to it.

#### HIGH-2: ...

### Non-findings considered

<brief: what you checked and ruled out — prevents repeat reviews>

### Out of scope

<what wasn't reviewed>
```

Offer to file as a GitHub issue — requires explicit confirmation per the outward-action rule. Sensitive findings should stay in `.gsd/security-reviews/` and not be pushed to a public tracker; check the repository's security policy first.

<!-- source: security-and-hardening | ## Red Flags | sha256: ed27406eb3d9481c1beb3f35b1fd42633bb657fda62cb8fb06f725efb479a1a7 -->

## Red Flags

- User input passed directly to database queries, shell commands, or HTML rendering
- A delete, move, or overwrite whose target comes from a payload, a config value, or another process's command line, guarded only by a shape check on the path
- Secrets in source code or commit history
- API endpoints without authentication or authorization checks
- Missing CORS configuration or wildcard (`*`) origins
- No rate limiting on authentication endpoints, or an in-memory limiter in front of more than one instance
- Stack traces or internal errors exposed to users
- Dependencies with known critical vulnerabilities, competing lockfiles at one installation boundary, non-reproducible installs, or blanket-approved scripts
- Server fetches user-supplied URLs without an allowlist (SSRF)
- LLM/model output passed into a query, the DOM, a shell, or `eval`
- Secrets, PII, or the full system prompt placed inside an LLM context window
- Personal data collected with no stated purpose, retention limit, or deletion path
- PII sent to analytics/ad/LLM vendors with no consent or data-processing agreement
- "Delete my account" that only flips a flag while the personal data lingers in stores and backups

<!-- source: security-and-hardening | ## Verification | sha256: 446d38f0b30e9fa1c46265ad7cd517f78149cb3613a9c1a72540072e52fbc13e -->

## Verification

After implementing security-relevant code:

- [ ] The native audit has no unmitigated reachable critical/high findings; CI preserves the authoritative lockfile and blocks unreviewed dependency scripts
- [ ] No secrets in source code or git history
- [ ] All user input validated at system boundaries
- [ ] Destructive filesystem operations resolve symlinks, then verify allowlisted root, minimum depth, and ownership before running
- [ ] Authentication and authorization checked on every protected endpoint
- [ ] Security headers present in response (check with browser DevTools)
- [ ] Error responses don't expose internal details
- [ ] Rate limiting active on auth endpoints, backed by a shared store when more than one instance serves traffic
- [ ] Server-side URL fetches validated against an allowlist (no SSRF)
- [ ] LLM/model output validated and encoded before use (if AI features present)
- [ ] Personal data is classified, minimized to a stated purpose, and has a retention limit
- [ ] Deletion and export requests work end-to-end (including backups, caches, and analytics copies)

