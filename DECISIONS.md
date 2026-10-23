# Decisions

Short architecture decision records. Each states the context, the decision, and the
consequence — including the cost.

---

## D1 — Put safety policy outside the LLM

**Context.** The model proposes tool calls and prose. It cannot be trusted to
enforce identity, confirmation, tenancy or grounding.

**Decision.** Enforce these in ordinary code around the model: session binding,
explicit SQL filters, PIN checks, output sanitisation, fixed escalation script.

**Consequence.** The model can be swapped or degraded without changing the security
contract. The policy layer must be maintained and tested separately; a bug there is
a real vulnerability, not a prompt-tuning issue.

---

## D2 — Speak only allow-listed tool facts

**Context.** Fluent models invent ETAs, tracking numbers and status words when a
tool fails or returns nothing.

**Decision.** For status intents, extract a fixed set of fact fields from a
successful tool result. If the result is missing/error/not-found, speak a fixed
escalation script. Add a lexical guard that blocks status-bearing prose without a
backing tool call.

**Consequence.** Answers are narrower and sometimes repetitive, but a failed lookup
cannot become a confident lie. The lexical guard is not a proof; paraphrase and
non-status claims remain a risk.

---

## D3 — Bind every authorisation factor to a supplier

**Context.** A session flag (`verified = true`) is not enough if the identified
supplier changes mid-call. A PIN for account A must not authorise a write for
account B.

**Decision.** Store the supplier ID alongside each factor at verification time.
Authorise only when the current `session.supplier_id` matches the stored binding.
Clear both factors when the identified supplier changes or becomes unresolved.

**Consequence.** Identity switching cannot inherit stale authority. The cost is more
state and explicit clearing paths. The private product still lacks a confirmation
gate; PIN binding is necessary but not sufficient.

---

## D4 — Sign the Lambda bridge and consume signatures once

**Context.** The API is reachable over HTTP. A forged turn could read data or write
without a phone call. A captured turn could be replayed.

**Decision.** HMAC-SHA256 over the request body, a 300-second freshness window, and
a one-time signature ledger. Use Redis atomic `SET NX EX` when configured so
multiple API instances share the ledger; fail closed in production if a configured
Redis is unreachable. Fall back to a process-local ledger only outside production.

**Consequence.** Forged and replayed turns are rejected under normal operation. The
system now depends on clock health, secret management and Redis availability. Key
rotation remains a manual runbook.

---

## D5 — Use explicit tenant filters, not RLS, as the primary control

**Context.** The app connects to Postgres with a role that bypasses row-level
security. RLS policies exist but are inert.

**Decision.** Require `tenant_id` predicates in every query and test known
cross-tenant paths. Treat RLS as future defence-in-depth, not current protection.

**Consequence.** The code is honest about where isolation comes from. A missed
predicate is a direct leak; the long-term fix is a non-bypass DB role plus enforced
RLS and query linting.

---

## D6 — Keep campaign and side-effect workers disabled by default

**Context.** Outbound campaigns and external side effects can harm people and
damage reputation if enabled before consent and provider checks are ready.

**Decision.** Ship the durable ledger, retries and dead-letter states, but require
an explicit per-tenant allow-list to run workers. Reject `"*"`. Hard-reject
outbound dialling.

**Consequence.** “Queued” is not “sent”, and the UI must say so. The product is less
impressive in a demo but much harder to misuse. Enabling a worker remains a
deliberate, auditable act.

---

## D7 — Build the public demo as a reconstruction, not an export

**Context.** Publishing production code would expose prompts, schemas, tenant logic
and provider configuration. Cleaning a wholesale copy is error-prone.

**Decision.** Start from an allow-list. Rebuild a small deterministic engine that
models the **target** contract, with synthetic fixtures. Label it as a
reconstruction everywhere. Publish short, non-secret excerpts separately.

**Consequence.** The demo does not prove production parity. It does make the safety
argument concrete and runnable. The private product’s missing gates are stated
explicitly rather than hidden by the demo.

---

## D8 — No real providers, audio or customer data in the public repo

**Context.** A public demo with keys, phone numbers or recordings is a breach waiting
to happen. Network calls also make reproduction fragile.

**Decision.** Stdlib-only Python, no network, no audio, no provider SDKs, no real
identifiers. Text turns and in-memory tools only.

**Consequence.** The demo cannot reveal STT/TTS/provider failures. It runs anywhere
in under a second, which is the right trade-off for a case study.

---

## D9 — Label weak evidence instead of hiding it

**Context.** Historical docs contain a 3-run mock benchmark, an empty-text load
test, and an all-fallback evaluation artifact. Quoting them would be misleading.

**Decision.** Publish the numbers **and** their methodology limits. State which
claims are forbidden. Make the evaluation page a first-class part of the case study.

**Consequence.** The project looks less polished but is credible under technical
review. Reviewers can reproduce the demo and see exactly what is not measured.

---

## D10 — Split the licence

**Context.** The documentation and excerpts are proprietary product material. The
demo is a small reference implementation intended to be run and learned from.

**Decision.** Root: all rights reserved, viewing/evaluation permitted. `demo/` and
synthetic fixtures: MIT. No licence permits cloning the private product or using the
VoxFlow name as a brand.

**Consequence.** Readers can run and reuse the demo; the product moat is not given
away. Any commercial use of the proprietary material needs written permission.

---

## D11 — Use a deterministic intent parser in the demo

**Context.** An LLM would add nondeterminism, keys, cost and a network dependency to
a safety demonstration.

**Decision.** Regex intent detection with explicit argument formats. Every scenario
is reproducible byte-for-byte.

**Consequence.** The demo tests policy, not language understanding. It cannot
estimate real intent accuracy. That limitation is stated rather than papered over.

---

## D12 — Validate results, not just inputs

**Context.** A tool can return `{}`, a partial row, or an error-shaped dict. The
model will fill gaps.

**Decision.** Each demo tool declares required result keys. Missing keys raise
`ResultRejected`; the turn escalates. The private product does not yet do this
consistently.

**Consequence.** Malformed upstream data cannot become speech. The cost is more
explicit tool contracts and a failure path for every tool.

---

## D13 — Fail closed on missing configuration

**Context.** Silent defaults (default tenant, unsigned webhooks, global allow-list)
turn a misconfiguration into a security incident.

**Decision.** Missing DID, tenant, secret, consent or tool result → reject or
escalate. No default tenant. No `"*"` allow-list. Unsigned webhooks rejected in
production.

**Consequence.** A misconfigured deployment drops calls instead of leaking data.
Operators need clear health checks and alerts; this is an accepted availability
cost.
