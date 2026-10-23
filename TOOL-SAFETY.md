# Tool safety

The product’s risk is not that the LLM is rude. It is that a fluent answer can be
wrong, or that a plausible sentence can authorise a write the caller never agreed
to. Tool safety is therefore the core of this case study.

> **Read this first:** the private product implements identity binding, tenant
> scoping, PIN authorisation for PO creation, and a spoken-output grounding guard.
> It does **not** yet implement a universal confirmation gate, shared argument/result
> schema validation, or idempotency for every write. The public demo implements the
> target contract so the missing gates are concrete and testable. Do not conflate
> the two.

---

## 1. Tool inventory

The private dispatch surface recognises 22 tool names. They fall into five classes:

| Class | Representative tools | Risk |
| --- | --- | --- |
| Read (internal) | `check_stock`, `check_po_status`, `get_order_details`, `get_shipment_status`, `verify_po` | Data disclosure across tenants/suppliers |
| Read (external) | `fetch_po_from_sheet` | Untrusted cell text entering the prompt |
| Identity | `lookup_supplier`, `verify_caller`, `verify_pin` | Account takeover, PIN brute force |
| Write (reversible) | `schedule_appointment`, `update_worksheet`, `edit_sheet_row` | Wrong slot, wrong row, duplicate side effect |
| Write (high impact) | `create_po` | Unauthorised purchase order |
| External message | `send_sms`, `send_email`, `send_whatsapp_message` | Data sent to the wrong recipient |
| Prohibited / disabled | `place_outbound_call`, refunds | Unauthorised outbound or money movement |
| Escalation | `escalate_to_human`, `request_callback` | Lost callback, PII in free text |

Private tool **schemas and implementations are not published**. The demo uses a
smaller synthetic tool set (`get_order_status`, `check_stock`,
`book_delivery_slot`, `update_order_status`, `send_sms`, `escalate_to_human`,
`issue_refund`).

---

## 2. The target contract

Every tool call passes through gates in this order:

```text
1. Tool allow-list        unknown name → refuse
2. Prohibited class       refund/outbound → refuse
3. Session validity       expired/terminated → refuse
4. Identity binding       factor bound to the same supplier → else refuse
5. PIN binding            high-impact writes only → else refuse
6. Argument schema        required keys, types, formats, no unknown keys → else reject
7. Confirmation           write args hash equals granted hash → else block
8. Idempotency            replay returns prior result, never a second write
9. Execution              tenant-scoped query / queued side effect
10. Result schema         required fields present → else reject and escalate
11. Untrusted-content     instruction-shaped tool text stripped, never executed
12. Grounded speech       only allow-listed fields may be spoken
```

This is the contract the demo enforces and tests. The private product implements
steps 1–5, 9, 11 (partially) and 12 (lexically); steps 6–8 and 10 are the gap.

---

## 3. Status by control

| Control | Private product | Public demo | Evidence |
| --- | --- | --- | --- |
| Unknown tool refused | Yes | Yes | Dispatch allow-list |
| Prohibited tool refused | Yes (`place_outbound_call` hard reject) | Yes (`issue_refund`) | Demo scenario |
| Tenant-scoped SQL | Yes, explicit `tenant_id` predicates | Fixture scoping | Private tests |
| Identity required for reads | Yes for sensitive reads | Yes | `_sensitive_read_denial` analogue |
| PIN required for PO creation | Yes, bound to supplier | Yes for status update | Excerpt 01 |
| Argument schema | **No** | Yes | Demo `validate_args` |
| Result schema | **No** | Yes | Demo `ResultRejected` |
| Caller confirmation | **No** | Yes | Demo confirmation hash |
| Idempotency | Tool-specific; PO/appointments not idempotent | Yes for writes | Demo duplicate scenario |
| Per-tool timeout | No (turn-level 6 s) | Simulated | Demo timeout scenario |
| Untrusted text stripped | Partial (prompt rules + output guard) | Yes | Demo injection scenarios |
| Grounded status speech | Yes (lexical guard) | Yes (allow-list) | Excerpt 02 |
| Audit denials | Partial (only some paths log) | Yes | Demo events |

### Why “PIN required” is not “confirmed”

A PIN proves the caller knows a secret. It does not prove the caller agreed to the
specific order, slot, quantity or status the model extracted. Without a
confirmation bound to the exact arguments, a misheard reference plus a valid PIN
can still create the wrong PO. This is the most important unresolved product risk.

### Why tenant filters are not RLS

The private app uses explicit `tenant_id` filters in every query and also ships
row-level-security policies. In the audited deployment, the application role
bypasses RLS, so the policies are inert. The filters are the real control. A single
missing predicate is a cross-tenant leak; tests cover known paths, not all future
queries.

---

## 4. Failure semantics

| Failure | Correct behaviour | Why |
| --- | --- | --- |
| Tool timeout | Escalate with fixed script | No partial fact may be spoken |
| Malformed result | Reject, escalate | Missing fields cannot be inferred |
| Not found | Say not found; offer escalation | Never “probably dispatched” |
| Identity mismatch | Re-ask once, then escalate | Do not confirm account existence |
| PIN mismatch | Re-ask once, then lock/escalate | Bound brute force |
| Caller declines | Write nothing; offer alternatives | Consent must be explicit |
| Caller changes args | Invalidate pending action | Stale “yes” must not apply |
| Session expires | Refuse; escalate | No writes after authority lapses |
| Call drops mid-write | Mark incomplete; reconcile | Never report success |

The fixed escalation script is deliberately repetitive:

> “I can't confirm that from the live records right now. I've raised it with the
> operations team and someone will call you back.”

---

## 5. Grounding

Two layers exist in the private product:

1. **`speak_from_tool(result)`** classifies a tool result. If it is an error, not
   found, or lacks usable facts, it returns the escalation script instead of prose.
2. **`sanitize_turn_reply(...)`** strips markup and reasoning, blocks status-bearing
   sentences when no successful status tool backs them, rewrites false sheet-write
   claims, and caps spoken output at two sentences.

This is a **lexical** control. It catches known status words (`eta`, `dispatched`,
`delivered`, `in stock`, `pallet`, `dock`, `bay`, …) but cannot prove that an
arbitrary sentence is grounded. A semantic entailment check is future work.

The public excerpt is
[code-walkthrough/02-grounded-speech.md](code-walkthrough/02-grounded-speech.md).

---

## 6. Prompt injection

The product has no instruction/data classifier. Mitigations are partial:

- System prompt tells the model to treat tool output as data.
- The output guard strips instruction-shaped strings in the demo.
- Tool arguments are constrained by function signatures and some format checks.
- Writes require identity; some require PIN.

Residual risk: a malicious sheet cell or caller utterance can still influence the
model’s choice of tool or arguments. The demo blocks a narrow regex set; that is a
demonstration, not a production classifier. See
[THREAT-MODEL.md](THREAT-MODEL.md#t3-prompt-injection).

---

## 7. Messaging and side effects

The private product’s SMS/WhatsApp/email tools **queue** notifications. The worker
does not have a configured provider; it marks notifications sent without sending
them (email is explicitly rejected as unconfigured). The UI/copy must not say a
message was delivered.

Sheet writes are queued through a durable ledger with retries and a tenant
allow-list. Tools return `queued`, `not_enabled`, `failed` or `logged` — never
`written`. A spoken-output guard rewrites “I’ve updated the sheet” when the write
failed or is only queued. One branch (`logged` after a swallowed enqueue failure)
can still produce a false claim; this is a known gap.

---

## 8. What the demo proves — and does not

**Proves**

- A write cannot execute without a confirmation whose argument hash matches.
- A declined confirmation writes nothing.
- A changed order invalidates a pending action.
- A duplicate request returns the prior result.
- A PIN for the wrong supplier cannot authorise a write.
- Timeout, malformed result, expiry and termination escalate.
- Instruction-shaped caller speech and tool output are blocked.
- SMS can only go to the verified caller’s number.
- The PIN never appears in audit events.

**Does not prove**

- That the private product enforces these gates today (it does not, for several).
- That the regex intent parser generalises to real speech.
- That the LLM cannot be injected in ways the regex misses.
- That writes are safe under concurrency in Postgres.
- That any provider actually delivers a message.

The tests are contract tests for the demo, not a security certification.
