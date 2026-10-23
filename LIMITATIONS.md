# Limitations

As of the audited commit `5acef5f` (2026-10-23). If code has moved since, re-audit;
this page is a snapshot, not a live guarantee.

The private product is a **supervised-pilot prototype**. It is not production-ready
for unsupervised writes. The demo is a **reference model**, not a mirror.

---

## 1. P0 product gaps

These block any claim of production readiness.

| # | Gap | Why it matters | Demo covers it? |
| --- | --- | --- | --- |
| 1 | **No universal caller confirmation gate** | A misheard reference plus a valid PIN can create the wrong PO; no second “yes” bound to arguments | Yes |
| 2 | **No shared argument/result schema** | Model-supplied args are splatted into functions; malformed results can reach speech | Yes |
| 3 | **No instruction/data separation** | Caller speech or a sheet cell can steer the model; no classifier or provenance | Partly (regex) |
| 4 | **PO/appointment writes are not idempotent** | A repeated request creates a duplicate record | Yes (demo writes) |
| 5 | **RLS policies are inert** | Tenant isolation depends on every query remembering `tenant_id` | No (single process) |
| 6 | **SMS/WhatsApp/email do not send** | Tools queue; worker marks sent without a provider; email is rejected as unconfigured | Demo models SMS, does not send |
| 7 | **Erasure is partial** | Sheet rows, logs, tool audit, backups and recordings can survive | No |
| 8 | **No barge-in / VAD on PSTN** | Caller cannot interrupt; long agent turns feel dead | No |
| 9 | **Benchmark and load test are mislabelled** | 822 ms is n=3 mock TTS; load test posts empty text | N/A |
| 10 | **Last eval artifact is all fallback** | 7/30 says nothing about model quality | N/A |

---

## 2. P1 product gaps

| Gap | Consequence |
| --- | --- |
| Turn-level 6 s timeout, no per-tool timeout | One slow sheet read can consume the whole turn |
| Some denial paths do not log | Probing protected reads is invisible |
| Sheet enqueue exceptions swallowed in one branch | A false “updated the sheet” can survive |
| No provider key rotation runbook | Compromise recovery is manual |
| No per-caller-number PIN throttling | Distributed attempts are harder to stop |
| No semantic grounding check | Lexical guard can be bypassed |
| Free-text logs and traces | Transcript/PII can leak to log stores |
| No deletion receipt | Erasure cannot be proven |
| No cost telemetry per call | Unit economics unknown |
| Limited live-provider testing | Sheets/Connect/Polly paths are mock-tested |

---

## 3. Capabilities that do not exist

Do not put these in copy, a resume, or a buyer deck:

<!-- safety-scan:ignore-claims-start -->
- Production readiness, uptime SLA, or on-call.
- SOC 2, ISO 27001, GDPR, PCI DSS, or “compliant”.
- Zero hallucination, 100% accuracy, or “never wrong”.
- Live PSTN latency, sub-400 ms turns, or “822 ms glass-to-glass”.
- Real customers, revenue, case studies, or named design partners.
- Real SMS, WhatsApp, email, or outbound dialling.
- Barge-in, full-duplex conversation, or voice biometrics.
- Complete erasure, “zero PII”, or data residency guarantees.
- Salesforce, SAP, Slack, Teams, NetSuite, or other invented integrations.
- Hindi as a marketed capability.
- Autonomous operation without a human hold point.
<!-- safety-scan:ignore-claims-end -->

---

## 4. Public demo limitations

| Limitation | Effect |
| --- | --- |
| Regex intent parser | Does not generalise to free speech; no LLM |
| No audio/STT/TTS | Cannot reveal recognition or prosody failures |
| In-memory state | No DB concurrency, retries, isolation or persistence |
| Plain fixture PINs | Demonstrates policy, not secure storage |
| Single process | Cannot demonstrate cross-tenant isolation |
| Small tool set | Not the private 22-tool surface |
| Synthetic data | No real distribution, accents, noise or adversarial callers |
| No durable jobs | Side-effect retry/dead-letter not modelled |
| Narrow injection regex | Bypassable; not a security control |
| No network | Cannot demonstrate provider integration |

The demo is deterministic on purpose. A passing run means “the contract is
internally consistent”, not “the product is safe”.

---

## 5. What the demo does prove

- The state machine can be expressed and tested without an LLM.
- Confirmation, PIN binding, idempotency and result validation are implementable
  and testable at the tool boundary.
- Failure paths can fail closed and produce an honest spoken message.
- A small stdlib test suite can cover the core safety contract.

That is the engineering argument: the missing production gates are not mysterious;
they are concrete and can be added.

---

## 6. Known inconsistencies in historical docs

The private repo contains “Complete” flags and marketing copy that outrun the code.
Treat them as historical claims, not truth. Specific examples:

- Benchmark/load-test labels overstate what was measured.
- Evaluation artifacts include fallback runs.
- Pricing and plan limits have appeared hardcoded in UI copy instead of the billing
  catalogue.
- “Sent” messaging status has been shown without a provider delivery.
- Privacy copy has implied stronger erasure than the code performs.

This public repo does not repeat those claims. If you find one here, it is a bug;
open an issue.

---

## 7. Safe description

> VoxFlow is a multi-tenant inbound voice-agent prototype for depot order and stock
> workflows. It has a real Connect/Lex ingress, identity and PIN binding,
> tenant-scoped tools, a grounded-speech guard, a durable job ledger with workers
> disabled, and a large regression suite. It is not production-ready for write
> actions, has no live task-quality or PSTN latency evaluation, and does not send
> real messages. The public demo is synthetic and demonstrates the target safety
> contract.
