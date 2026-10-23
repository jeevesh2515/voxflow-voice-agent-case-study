# Call flow

A turn is one caller utterance and one agent reply. This document follows the
private product’s PSTN path and notes where the public demo differs. It does not
describe audio internals in detail because the API never sees PSTN audio.

![Call State Machine](diagrams/02-state-machine.svg)

---

## 1. Ingress

```text
PSTN caller
  → Amazon Connect contact flow (UK DID)
  → Lex V2 speech capture (en-GB)
  → transcript
  → Lambda bridge
      - reads ContactId, caller number, system number, transcript
      - signs the body with HMAC-SHA256
      - POST /api/connect/turn
  → FastAPI
```

Controls at ingress:

- **Exact DID routing.** The called number must map to an active tenant phone
  number. Unknown DIDs fail closed; there is no fallback tenant.
- **Signature verification.** The API recomputes the HMAC, checks a timestamp
  window, and consumes the signature once through a replay ledger.
- **Tenant resolution before prompt assembly.** No tenant means no LLM call.

The Lambda bridge and signature check are the only inbound trust boundary between
telephony and the application. A bug here drops live calls, so it has dedicated
tests.

---

## 2. Session load

The API loads or creates a `CallSession` keyed by the telephony contact ID. It
carries:

- tenant, supplier and caller identifiers
- verification and PIN flags, plus the supplier each factor is bound to
- route policy (DID, language, recording/consent flags)
- turn history and tool actions
- escalation reason and outcome

Sessions expire. An expired session cannot execute tools; the call escalates.

---

## 3. Consent and greeting

The first agent turn:

1. Plays the recording/assistance notice if the tenant requires it.
2. Asks for the account reference and a corroborating factor.
3. Refuses to discuss order data before identity is bound.

Consent state is stored per call. A missing consent flag does **not** silently
default to “granted” in code paths that gate recording; deployment defaults are
explicit configuration.

---

## 4. Identity

```text
caller: “It's Demo Depot Alpha, Manchester.”
agent:  “Thank you. I've verified the account. How can I help?”
```

The private product supports knowledge factors (company + city/VAT/contact name)
and an optional PIN. Rules:

- Factors must match the same supplier record.
- A mismatch does not reveal whether the account exists.
- Two failed identity attempts escalate.
- Verification is scoped to the call, not persisted across calls.
- PIN verification is separate from knowledge verification and has its own attempt
  limit and lockout.

`Demo Depot Alpha` and `Manchester` are synthetic examples. Real customer data is
not in this repository.

---

## 5. Intent and argument extraction

The LLM proposes a tool call. Before execution, the private product currently
checks:

- the tool exists in the allow-list;
- the session is verified (for sensitive reads);
- the session is PIN-verified (for PO creation);
- the called supplier is the authorised supplier;
- SQL is tenant-scoped.

It does **not** currently validate a shared argument schema, reject unknown
arguments, or validate the result shape. The public demo adds those checks to show
the target contract:

```python
validate_args(spec, args)          # required/optional keys, formats, unknown keys
...
result = self._result(spec, data)  # required result keys, else ResultRejected
```

---

## 6. Tool execution

```text
agent → tool runtime
          ├─ policy check (identity / PIN / tenant)
          ├─ argument validation      [demo only]
          ├─ confirmation check       [demo only]
          ├─ idempotency lookup       [demo; partial in product]
          ├─ execute (Postgres / Sheets / side effect)
          └─ result validation        [demo only]
agent ← {ok, data} or typed failure
```

Failure classes:

| Failure | Behaviour |
| --- | --- |
| Unknown tool / prohibited tool | Refuse; never execute |
| Missing identity or PIN | Refuse; ask again or escalate |
| Invalid arguments | Reject; re-ask (demo) / model retry (product) |
| Timeout | Escalate with the fixed script |
| Malformed result | Reject; escalate |
| Call terminated mid-execution | Never report success |
| Session expired | Refuse; escalate |

The fixed script is intentionally boring:

> “I can't confirm that from the live records right now. I've raised it with the
> operations team and someone will call you back.”

It is used whenever the agent cannot ground a status claim. It does not invent an
ETA, a tracking number, or a successful write.

---

## 7. Confirmation and PIN

Target contract (implemented in the demo, **not yet universal in the product**):

```text
caller: “Book PO-SYN-1001 into 2026-10-25T09:00Z.”
agent:  “I can book PO-SYN-1001 into 2026-10-25T09:00Z. Shall I confirm?”
caller: “Yes.”
agent:  “Booked. The reference is BK-5044A0.”
```

Rules:

- The confirmation prompt contains the exact arguments.
- “Yes” is bound to a hash of those arguments.
- If the caller changes the order reference, the pending action is invalidated.
- A decline writes nothing.
- A repeated identical request returns the prior result; it does not write twice.
- A high-impact write additionally requires a PIN bound to the same supplier, and
  asks for confirmation **after** the PIN succeeds.

If the caller says “yes” to a different question, the hash does not match and the
write does not execute.

---

## 8. Grounded speech

Only allow-listed fields may be spoken for status intents: status, PO signed flag,
quantity, ETA, dispatch date, expected delivery, total, availability, appointment
ID. The private product implements this in two layers:

1. `speak_from_tool()` returns either a fact string or the escalation script.
2. `sanitize_turn_reply()` blocks status-bearing prose when no successful status
   tool call backs it.

```text
tool result: {ok: true, status: "dispatched", eta: "2026-10-24"}
spoken:      “Order PO-SYN-1001 is dispatched. The latest ETA is 2026-10-24.”

tool result: timeout
spoken:      “I can't confirm that from the live records right now…” 
```

This is a **lexical** guard, not a semantic proof. It reduces a known failure mode;
it does not make hallucination impossible.

---

## 9. Escalation and closure

Escalation creates a callback record with a reason, call ID and tenant. The caller
hears the fixed script. The outcome is persisted even if the call drops.

Closure:

- The agent can close on “bye”, “that's all”, or similar.
- Tool actions and confirmation events are stored with the outcome.
- A call that ends mid-turn is marked incomplete, not resolved.

Escalation is a success path when the agent cannot ground an answer. The demo’s
9 escalations out of 21 scenarios are expected outcomes, not failures.

---

## 10. What the caller never hears

- Raw tool JSON, stack traces, provider errors, or internal IDs beyond the booking
  or ticket reference.
- A status word that did not come from a successful status tool result.
- A claim that a sheet, message, or record was updated when the write failed or was
  only queued.
- A PIN echoed back, logged, or included in persisted actions.

---

## 11. Timing

The private turn deadline is **6 seconds** with a maximum of **5** LLM/tool
iterations. Exceeding the deadline escalates.

This is a runtime guardrail, not a latency result. The only public latency numbers
in the private repo are a 3-run mock-TTS benchmark and a load test that posted empty
transcripts; neither measures live PSTN turn latency. See
[EVALUATION.md](EVALUATION.md#5-what-not-to-cite).

---

## 12. Differences in the public demo

| Stage | Private product | Demo |
| --- | --- | --- |
| Audio / STT / TTS | Connect, Lex, Polly, Groq Whisper | None |
| Intent parsing | LLM function calling | Deterministic regex |
| Identity | DB-backed supplier factors | Fixture comparison |
| PIN | PBKDF2 hash in DB | Plain fixture value |
| Confirmation | Missing | Enforced for writes |
| Schema validation | Missing | Enforced |
| Idempotency | Tool-specific | Enforced for idempotent tools |
| Persistence | Postgres / Sheets | In-memory |
| Escalation | Callback record | Audit event |

The demo exists to make the contract executable. It is not a mirror of production
behaviour.
