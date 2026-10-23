# VoxFlow — inbound voice agent for depot operations

**Public engineering case study · synthetic demo · no customer data**

> VoxFlow is an inbound voice agent for UK FMCG, road-freight and pallet-depot
> operations. It answers supplier calls, verifies the caller, looks up order and
> stock facts through tools, and escalates when it cannot ground an answer.
> This repository is a sanitized case study, not the production system.

**Status:** private product is a supervised-pilot prototype, **not production-ready
for write actions**. Nothing here is a live service, a customer deployment, or a
compliance certification.

---

## What this repository is — and is not

| This repository | The private product |
| --- | --- |
| Architecture notes, sanitized code excerpts, diagrams | Full FastAPI + Next.js application |
| A deterministic, dependency-free **synthetic demo** | Amazon Connect / Lex V2 / Groq / Polly path |
| 21 synthetic call scenarios, 19 contract tests | 963-test backend suite on the audited commit |
| Fake accounts, orders, PINs and tool results | Tenant data, provider config, prompts, schemas |
| Documents known gaps openly | Same gaps, plus operational code not shown here |

The runnable demo is a **reconstruction of the documented safety contract**, not an
extract of the production engine. It exists so a reader can observe the state
machine, confirmation gate, PIN binding, idempotency and grounding rules without
provider accounts, audio, or network access. Some of those gates are **not yet
implemented in the private product** — [LIMITATIONS.md](LIMITATIONS.md) lists exactly
which. Do not read the demo as a claim of production parity.

---

## The problem

A depot operations desk spends its day on the same inbound questions:

- “Where is PO 4471?”
- “Is it signed?”
- “Do you have 12 pallets of cartons?”
- “Can you book us into the 09:00 slot?”
- “Can I change the delivery status?”

The answers live in an order system, a stock sheet, or a mailbox. The caller is
often a supplier or driver, not a known user. A wrong status or an unauthorised
write is worse than a transfer to a human.

VoxFlow targets that workflow: **read-heavy, identity-bound, grounded in tool
results, and honest when a tool fails.** It is deliberately not a general-purpose
autonomous agent.

---

## What the agent does

1. Answers a UK inbound call through Amazon Connect + Lex V2 (`en-GB`).
2. Verifies the caller with two factors and optionally a 4–8 digit PIN.
3. Resolves intents against a bounded tool surface: order status, shipment, stock,
   order details, appointment slots, PO creation, messaging, sheet writeback, and
   human escalation.
4. Speaks only allow-listed facts returned by a successful tool call; otherwise it
   uses a fixed escalation script.
5. Records call outcome and tool events, and escalates to a callback queue.
6. Keeps tenants separate with explicit `tenant_id` filters and exact-DID routing.

---

## Verified evidence

Measured on the private repository at branch `bulletproof-sprint`, commit `5acef5f`,
2026-10-23. These are historical snapshots, not continuously updated badges.

| Check | Result | Scope |
| --- | --- | --- |
| Backend test suite | **963 passed, 1 skipped** in 133.29 s | Private repo, full `pytest` |
| Lint | `ruff` clean | Private API |
| Demo contract tests | **19 passed** | This repo, stdlib only |
| Synthetic scenarios | **21**, expected-outcome match **1.0** | This repo |
| Writes in demo | **4 executed, 4 confirmed**, compliance **1.0** | This repo |
| Adversarial cases | **2 injections blocked, 3 tool failures escalated** | This repo |
| Duplicate protection | **1 duplicate write suppressed** | This repo |

The demo summary is generated, not hand-written:

```bash
python3 demo/simulate_call.py --all
```

See [EVALUATION.md](EVALUATION.md) for methodology and for the measurements that
must **not** be cited (a mock benchmark and an empty-text load test).

---

## Architecture

![Voice pipeline: PSTN and browser paths](diagrams/01-voice-pipeline.svg)

```
Caller ──PSTN──► Amazon Connect (eu-west-2) ──► Lex V2 en-GB
                     │                              │ transcript
                     │ recording                    ▼
                     │                    Lambda bridge (HMAC-SHA256)
                     │                              │ POST /api/connect/turn
                     ▼                              ▼
              S3 + recording Lambda        FastAPI + AgentRunner
                                                    │
          ┌─────────────────────────────────────────┼───────────────────────┐
          ▼                    ▼                    ▼                       ▼
   Postgres (tenant)     Groq Whisper         Groq gpt-oss-20b        Google Sheets
   calls / logs /        (STT, server)        (+ fallbacks)           (tenant mirror,
   tool audit                                                          allow-list)
                                                    │
                                                    ▼
                                          reply text → Connect → Polly
```

The API never receives PSTN audio. Connect/Lex produce the transcript, the Lambda
bridge signs the turn, and the API returns text for Polly to speak. The browser
simulator is a second ingress and is **not** the PSTN path.

More: [ARCHITECTURE.md](ARCHITECTURE.md) · [CALL-FLOW.md](CALL-FLOW.md) ·
[diagrams/](diagrams/)

---

## Conversation state

![Call state machine](diagrams/02-state-machine.svg)

Identity is established before any order data is read. A second failed identity
attempt escalates. Unknown intent twice escalates rather than guessing. Tool
failure, malformed results, timeout, session expiry and mid-call termination all
fail closed.

The public demo implements the full state machine shown above. The private product
implements identity, intent routing, tool grounding, escalation and session
persistence, but **not** the universal confirmation gate or argument schema
validation shown in the target contract. That difference is deliberate and
documented.

---

## Tool-safety contract

| Tool class | Examples | Required gates in the target contract | Private product today |
| --- | --- | --- | --- |
| Read | order status, shipment, stock | verified identity, tenant-scoped query, schema-checked args | Implemented, tested |
| Reversible write | book slot, update status | confirmation bound to exact arguments, idempotency | **Confirmation/idempotency missing** |
| High-impact write | create PO, change status | PIN bound to the same supplier **and** confirmation | PIN implemented; confirmation missing |
| External | SMS to caller | verified recipient, confirmation | Messaging is simulated/recorded, not sent |
| Prohibited | refunds, money movement | never executable | Refused / out of scope |
| Escalation | callback ticket | reason + auditable event | Implemented |

The demo enforces every gate in the middle column. The private product enforces
identity, tenant scoping, PIN binding for PO creation and a spoken-output grounding
guard, but executes writes on model-supplied arguments without a second “yes”.
See [TOOL-SAFETY.md](TOOL-SAFETY.md) and [THREAT-MODEL.md](THREAT-MODEL.md).

---

## Example synthetic conversation

From `booking_requires_confirmation` (`python3 demo/simulate_call.py --scenario
booking_requires_confirmation --trace`):

```text
caller: account acct_synthetic_001 postcode M1 4AB
agent : Thank you, I've verified the account. How can I help with your order or delivery?
caller: book a slot for PO-SYN-1001 on 2026-10-25T09:00Z
agent : I can book PO-SYN-1001 into 2026-10-25T09:00Z. Shall I confirm that booking?
caller: yes
agent : Booked. The reference is BK-5044A0 for 2026-10-25T09:00Z.
```

Audit events show the order: `confirmation_requested` → `confirmation_granted`
(both with the same argument hash) → `tool_request` → `tool_result(confirmed=true)`.
The PIN never appears in the audit log. Full trace:
[assets/trace-example.txt](assets/trace-example.txt).

---

## Evaluation summary

| Measurement | Value | What it means |
| --- | --- | --- |
| Scenario expectations | 21/21 match | The demo behaves as its fixtures specify |
| Resolved / escalated | 12 / 9 | Every escalation is an expected fixture, not a failure |
| Write confirmation compliance | 1.0 (4/4) | No synthetic write ran without a matching confirmation |
| Prompt injections blocked | 2 | One in caller speech, one in tool output |
| Tool failures handled | 3 | Timeout, malformed result, termination |
| Backend tests (private) | 963 passed, 1 skipped | Historical snapshot, not this repo |

**Not measured:** live PSTN latency, speech-recognition accuracy, LLM answer
quality, customer outcomes, cost per call, or production reliability. The private
repo’s 822 ms benchmark used mock TTS and n=3; its load test posted empty text.
Neither is evidence of live latency. [EVALUATION.md](EVALUATION.md) explains both.

---

## Quickstart

Requires Python 3.10+. No packages, keys, network, audio or database.

```bash
git clone <this-repo-url>
cd voxflow-case-study

# Run every synthetic scenario
python3 demo/simulate_call.py --all

# Inspect one transcript and its audit events
python3 demo/simulate_call.py --scenario pin_gated_status_change --trace

# Run the contract tests
python3 -m unittest discover -s tests/sanitized-demo -v

# Public-safety scan + tests + link check
./scripts/verify.sh
```

Expected summary: 21 scenarios, 12 resolved, 9 escalated, 4 writes, 4 confirmed,
1 duplicate suppressed, 2 injections blocked, 3 tool failures.

More: [DEMO.md](DEMO.md)

---

## Repository map

```text
README.md                 This overview
ARCHITECTURE.md           Components, boundaries, deployment shape
CALL-FLOW.md              Turn-by-turn call lifecycle
TOOL-SAFETY.md            Tool classes, gates, and known gaps
THREAT-MODEL.md           Assets, actors, threats, residual risk
PRIVACY-AND-DATA.md       Data categories, lifecycle, erasure limits
EVALUATION.md             What was measured, and what was not
LIMITATIONS.md            Product gaps and demo limits
DECISIONS.md              Engineering decisions and trade-offs
DEMO.md                   Simulator guide and scenarios
SECURITY.md               Reporting policy and security posture
CONTRIBUTING.md           Contribution and claims rules
POSITIONING.md            Resume, LinkedIn and buyer copy
code-walkthrough/         Short sanitized excerpts with commentary
demo/                     Deterministic simulator (MIT)
fixtures/synthetic/       Fake accounts, orders, scenarios
tests/sanitized-demo/     19 contract tests
diagrams/                 Mermaid sources + rendered SVGs
assets/                   Generated trace and result JSON
scripts/                  Verification, safety scan, link check
docs/                     Evidence log, claims matrix, acceptance checklist
```

---

## What is deliberately not included

Production source code, private system prompts, tool schemas, provider
configuration, API keys, database dumps, customer records, transcripts,
recordings, phone numbers, internal hostnames, pricing configuration, billing
identifiers, deployment state, and private infrastructure. The public repo contains
short excerpts only where the technique is safe to show.

No production system is reachable from this repository, and the demo makes no
network calls.

---

## Honest claims

**Safe to say**

- Built a multi-tenant inbound voice agent for depot order and stock workflows.
- Implemented Amazon Connect/Lex ingress behind an HMAC-signed Lambda bridge.
- Implemented two-factor identity plus PBKDF2 PIN verification with lockout and log
  redaction, bound to the same supplier record.
- Implemented a spoken-output grounding guard that refuses unbacked status claims.
- Built a durable job ledger with workers disabled by default.
- Wrote and passed 963 backend tests at the audited commit.
- Built a synthetic, dependency-free simulator with 21 scenarios and 19 tests.

**Not safe to say**

<!-- safety-scan:ignore-claims-start -->
- Production-ready, compliant, certified, autonomous, or zero-hallucination.
- Live PSTN latency, sub-400 ms turns, or “822 ms glass-to-glass”.
- Real customers, revenue, case studies, or named design partners.
- Real SMS, email, outbound dialling, barge-in, or complete erasure.
- SOC 2, GDPR, PCI DSS, ISO 27001, or “zero PII”.
<!-- safety-scan:ignore-claims-end -->

Full matrix: [docs/claims-matrix.md](docs/claims-matrix.md)

---

## Resume bullet

> Built a multi-tenant inbound voice agent for UK depot operations using FastAPI,
> Amazon Connect/Lex V2, Groq STT/LLM and Postgres, implementing HMAC-signed
> telephony ingress, PBKDF2 caller-PIN binding, tenant-scoped tool calls and a
> grounded-speech guard, with 963 backend tests passing and a 21-scenario synthetic
> safety simulator covering confirmation, idempotency, injection and tool failure.

## LinkedIn summary

> VoxFlow is an inbound voice agent for structured depot workflows: order status,
> stock, shipment and appointment calls. I built the telephony bridge, identity and
> PIN binding, tool layer, grounding guard, durable job ledger and evaluation
> harness. The public case study uses synthetic calls and a deterministic simulator;
> the private product remains a supervised pilot, not an autonomous production
> service.

## Buyer demonstration

A supervised walkthrough of the private system is available to buyers on request.
It covers the audited workflow, the known gaps, and the pilot preconditions. No
contact details or customer references are published in this repository.

Read [POSITIONING.md](POSITIONING.md) for the longer buyer pitch and pilot scope.

---

## Licence

Root documentation, diagrams and code excerpts: **proprietary, all rights reserved**,
with permission to view and evaluate. The `demo/` directory and synthetic fixtures
are **MIT**. See [LICENSE](LICENSE) and [demo/LICENSE](demo/LICENSE).

You may read this repository to evaluate the work. You may not copy the proprietary
material into a competing product, resell it, or present it as your own.
