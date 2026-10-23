# Security policy

## Scope

This repository is a **case study**. It contains:

- documentation, diagrams and short sanitized excerpts;
- a synthetic, offline demo with no network access;
- synthetic fixtures and contract tests.

It does **not** contain the production service, provider credentials, customer data,
private prompts, deployment configuration, or a running endpoint.

Security reports about the **public repository** (for example, a secret accidentally
committed here, or a vulnerability in the demo) are in scope. Reports about the
private production system are handled separately by the owner and are not described
by this policy.

---

## Reporting a vulnerability

Once this repository is published, use **GitHub private vulnerability reporting**
on the repository’s Security tab. Do not open a public issue for a suspected secret
or exploit.

Please include:

- what you found and where (file, commit, line);
- why it matters;
- a minimal reproduction, if safe;
- whether any real data or credential is exposed.

Do **not** include live secrets, customer data, recordings, or exploit payloads
against third-party systems in the report. If a secret is exposed, report the
location only; the owner will rotate it.

There is no bug bounty and no guaranteed response time. Reports are reviewed as
soon as practical. Please allow time for a fix before public disclosure.

---

## Safe harbour

Good-faith research on this repository is welcome if it:

- stays within this repository and the local demo;
- does not access, modify or exfiltrate real data;
- does not attack providers, customers or infrastructure;
- does not run denial-of-service or spam campaigns;
- gives the owner reasonable time to respond.

This is not a legal safe-harbour agreement; it is the expected conduct.

---

## What is intentionally absent

| Item | Why |
| --- | --- |
| `.env` files / live keys | Would grant access to real systems |
| Production hostnames and account IDs | Infrastructure disclosure |
| Customer names, numbers, transcripts, recordings | Personal/commercial data |
| Private prompts and tool schemas | Product IP and attack surface |
| Billing identifiers | Financial configuration |
| Terraform state | Contains account/resource identifiers |
| Database dumps | Personal data |

The public repo is scanned for these before any visibility change. See
[docs/acceptance-checklist.md](docs/acceptance-checklist.md).

---

## Security design summary

The private product’s controls are described in
[ARCHITECTURE.md](ARCHITECTURE.md), [TOOL-SAFETY.md](TOOL-SAFETY.md) and
[THREAT-MODEL.md](THREAT-MODEL.md). The strongest implemented controls are:

- exact-DID tenant routing with no default tenant;
- HMAC-signed Connect turns with a freshness window and replay ledger;
- two-factor identity bound to a supplier record;
- PBKDF2-HMAC-SHA256 PIN storage with lockout and redaction;
- explicit `tenant_id` filters on queries;
- a spoken-output grounding guard and fixed escalation script;
- workers and outbound dialling disabled by default.

Known gaps are listed in [LIMITATIONS.md](LIMITATIONS.md). The most important are the
missing universal confirmation gate, missing argument/result schema validation,
incomplete instruction/data separation, inert RLS, simulated messaging, and partial
erasure.

Do not describe this project as “secure”, “compliant”, “certified” or
“production-ready” on the basis of this repository.

---

## Demo security

The demo:

- makes no network calls;
- reads only files inside this repository;
- uses synthetic identifiers;
- stores state in memory;
- exits non-zero when a scenario expectation fails.

It is safe to run in CI. It is not a sandbox for untrusted input: the regex parser
and in-memory tools are not hardened against adversarial files. Do not point it at
real data.

---

## Dependency and secret checks

The demo has **zero third-party Python dependencies**, so there is no package
lockfile to audit. CI runs:

- `scripts/verify-public-safety.sh` (secret/pattern/claim scan with a self-test);
- `scripts/check_links.py` (relative Markdown links);
- the contract tests and the full scenario run;
- `python3 -m compileall` as a syntax/build check.

Before publication, the owner should also run a full-history secret scan on the
staging repository. A clean current tree is not enough if private material exists in
history.
