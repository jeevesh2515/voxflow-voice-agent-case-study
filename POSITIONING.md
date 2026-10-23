# Positioning

Copy for a resume, LinkedIn, and buyer conversations. Every claim here is backed by
[EVALUATION.md](EVALUATION.md) or the private audit. Do not add outcomes that were
not measured.

---

## One-sentence value proposition

> VoxFlow answers structured inbound depot calls — order status, stock, shipments
> and appointment changes — with identity-bound tools, grounded answers, and a human
> escalation path when the records cannot support a reply.

---

## Resume bullet

> Built a multi-tenant inbound voice agent for UK depot operations using FastAPI,
> Amazon Connect/Lex V2, Groq STT/LLM and Postgres, implementing HMAC-signed
> telephony ingress, PBKDF2 caller-PIN binding, tenant-scoped tool calls and a
> grounded-speech guard, with 963 backend tests passing and a 21-scenario synthetic
> safety simulator covering confirmation, idempotency, injection and tool failure.

Why this is safe:

- “Multi-tenant”, “HMAC”, “PBKDF2”, “tenant-scoped”, “grounded-speech guard” are all
  implemented and evidenced.
- “963 backend tests passing” is a dated snapshot at commit `5acef5f`.
- “21-scenario synthetic safety simulator” is this repository and reproducible.
- It does **not** claim production, customers, revenue or latency.

Shorter variant:

> Built a multi-tenant inbound voice agent for depot order and stock workflows, with
> signed telephony ingress, PIN-bound authorisation, grounded tool answers and 963
> passing backend tests.

---

## LinkedIn project description

> VoxFlow is an inbound voice agent for structured depot workflows: order status,
> stock, shipments and appointment calls. I built the telephony bridge, caller
> identity and PIN binding, tenant-scoped tool layer, grounded-speech guard, durable
> job ledger and regression suite. The public case study uses synthetic calls and a
> deterministic simulator; the private product is a supervised pilot, not an
> autonomous production service.

---

## Buyer pitch

### 30 seconds

> Your ops desk answers the same order and stock questions all day. VoxFlow answers
> them on the phone: it verifies the caller, looks up the record through a bounded
> tool, and speaks only what the record supports. If the lookup fails or the caller
> wants a change, it escalates with a callback instead of guessing. It runs on Amazon
> Connect in the UK, and it is designed for supervised operation first.

### Two minutes

> The workflow is inbound, not outbound. A supplier or driver calls a depot number.
> Connect and Lex turn speech into text; a signed bridge sends the turn to the agent.
> The agent verifies the caller against the supplier record, optionally with a PIN,
> then answers from a small set of tools: order status, shipment, stock, order
> details, appointments.
>
> The important part is what it refuses to do. It does not answer from model memory.
> Status facts come from a successful tool result. If the tool times out, returns a
> malformed record, or cannot find the order, the caller hears an honest escalation
> script and a callback is raised. Writes are the higher-risk path: the target
> contract requires a confirmation bound to the exact arguments, a PIN bound to the
> same supplier for high-impact changes, and idempotency so a repeated request does
> not duplicate the action.
>
> The private build has the telephony path, identity and PIN binding, tenant-scoped
> tools, grounding guard, durable job ledger and a 963-test suite. It is not yet
> production-ready: the universal confirmation gate, shared schema validation and
> full instruction/data separation are still open. The public demo makes those gaps
> concrete and testable.
>
> A pilot would start read-heavy: order status and stock, one depot, one DID, human
> review of every call, workers and outbound disabled. Writes would stay off until
> confirmation, idempotency and reconciliation are proven.

### Problem / solution / evidence

| Problem | VoxFlow response | Evidence |
| --- | --- | --- |
| Repetitive status calls consume the ops desk | Bounded read tools for order, shipment and stock | 22-tool private surface; demo reads |
| A fluent model invents ETAs | Allow-listed facts + fixed escalation script | Excerpt 02; demo timeout/malformed scenarios |
| Callers are not authenticated users | Two factors + optional PIN bound to supplier | Excerpt 01; private tests |
| A wrong write is worse than a transfer | PIN for PO creation; target confirmation + idempotency | Demo; private gap stated |
| Cross-tenant leakage | Exact-DID routing, explicit `tenant_id` filters | Private tests; threat model |
| Provider outages drop calls | Turn deadline, fallback providers, escalation | Private runtime; demo failure paths |
| “Sent” messages that never sent | Queue + dry-run, workers disabled, honest status | Private jobs; limitations |

Do **not** add a financial savings column. No measured customer outcome exists.

---

## Target buyer

- Operations lead or founder at a UK FMCG distributor, road-freight carrier, or
  pallet depot.
- 5–50 people on the inbound desk; high call volume, repetitive status questions.
- Uses an order system or spreadsheet that can expose read APIs or a controlled
  sheet.
- Cares more about correct answers and auditability than about a flashy demo.

Not a fit: businesses wanting outbound sales calls, autonomous refunds, or a
general-purpose “AI employee”.

---

## Pilot scope

**In scope**

- One depot, one UK DID, one tenant.
- Read-only: order status, shipment status, stock.
- Human review of every transcript and escalation.
- Explicit consent/recording configuration.
- A named operations owner and a rollback path to the existing phone flow.

**Out of scope until proven**

- PO creation, status changes, sheet edits, messaging.
- Outbound campaigns or callbacks.
- Multi-site routing, SSO, Salesforce/SAP integrations.
- Any claim of compliance or autonomous operation.

**Success measures** (define before the pilot)

- grounded-answer accuracy against the source record;
- escalation precision/recall;
- caller completion without human transfer;
- p50/p95 turn latency on PSTN;
- unauthorised/duplicate write rate (target: zero in a supervised run);
- cost per call.

No savings claim until measured with the pilot.

---

## Discovery questions

1. Which five questions dominate the inbound queue?
2. Where do the answers live, and can we read them with a scoped credential?
3. How does a caller prove they are allowed to hear the answer?
4. Which actions are read-only, reversible, or high-impact?
5. Who reviews calls, and what is the rollback path?
6. What retention and consent rules apply to recordings and transcripts?
7. What would make you stop the pilot?

---

## What not to say

<!-- safety-scan:ignore-claims-start -->
- “Production-ready”, “enterprise-grade”, “compliant”, “certified”.
- “Zero hallucination”, “100% accurate”, “autonomous”.
- “Live UK depots”, “customers”, “revenue”, “case studies”.
- “822 ms”, “sub-400 ms”, “real-time at scale”.
- “We send SMS/email/WhatsApp” or “we dial out”.
- “Barge-in”, “full duplex”, “voice biometrics”.
- “GDPR-ready”, “zero PII”, “complete erasure”.
<!-- safety-scan:ignore-claims-end -->

If a buyer asks for proof, show the demo, the test output, and the limitations page.
That is the differentiator: the boundaries are explicit.
