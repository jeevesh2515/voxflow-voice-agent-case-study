# Claims matrix

Every public claim about VoxFlow must map to a row here. Status vocabulary:

- **VERIFIED** — reproducible in this repository.
- **VERIFIED SNAPSHOT** — measured once on the private repo; dated, not live.
- **IMPLEMENTED** — code reviewed and covered by tests.
- **IMPLEMENTED, EXTERNALLY UNVERIFIED** — code exists; live provider not exercised.
- **PARTIAL** — exists for some paths, not all.
- **PROTOTYPE / MOCK** — no real provider or delivery.
- **NOT IMPLEMENTED / NOT MEASURED** — must be described as absent.
- **FORBIDDEN — do not use** — contradicted by evidence.

| Claim | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Multi-tenant inbound voice agent for depot workflows | IMPLEMENTED | Private audit; tenant filters; README | Real codebase, supervised prototype |
| Amazon Connect + Lex V2 ingress (`en-GB`, `eu-west-2`) | IMPLEMENTED, EXTERNALLY UNVERIFIED | Architecture; private bridge tests | Contact flow and bot config not in repo |
| HMAC-signed Lambda bridge | IMPLEMENTED | Excerpt 04; private bridge tests | Shared secret; no rotation runbook |
| Replay-resistant turns | IMPLEMENTED | Excerpt 04; Redis `SET NX EX`; fail closed | In-memory fallback outside production |
| Exact-DID tenant routing | IMPLEMENTED | Private route tests; architecture | No default tenant |
| Two-factor caller identity | IMPLEMENTED | Excerpt 01; private tests | Knowledge factors can be social-engineered |
| PBKDF2-HMAC-SHA256 PIN storage (310k iterations) | IMPLEMENTED | Excerpt 01 | 4–8 digits remains a weak secret |
| PIN bound to the same supplier | IMPLEMENTED | Excerpt 01; private tests | Necessary, not sufficient for writes |
| PIN attempt limits and persistent lockout | IMPLEMENTED | Private tests | Distributed attempts not fully throttled |
| PIN redaction from logs/tool JSON | IMPLEMENTED | Excerpt 01; private tests | Backstop, not permission to log speech |
| Explicit `tenant_id` query filters | IMPLEMENTED | Excerpt 03; private tests | Every new query must remember |
| Row-level security enforced | FORBIDDEN — do not use | Private audit | Policies exist but are inert; do not claim RLS protection |
| 22-tool agent surface | IMPLEMENTED | Private audit | Schemas not public |
| Grounded status speech | IMPLEMENTED | Excerpt 02; private tests | Lexical guard, not semantic proof |
| Universal caller confirmation gate | NOT IMPLEMENTED | Private audit; demo only | Top unresolved product risk |
| Shared argument/result schema validation | NOT IMPLEMENTED | Private audit; demo only | Model args are not schema-checked |
| Write idempotency | PARTIAL | Private audit; demo | PO/appointments can duplicate |
| Durable job ledger | IMPLEMENTED | Architecture; private tests | Workers disabled by default |
| Real SMS / WhatsApp / email delivery | PROTOTYPE / MOCK | Private audit | Queued; worker marks sent without provider |
| Outbound dialling | NOT IMPLEMENTED | Private audit | Hard-rejected; adapter disabled |
| Barge-in / full duplex | NOT IMPLEMENTED | Private audit | Caller cannot interrupt |
| 963 backend tests passing | VERIFIED SNAPSHOT | Private run 2026-10-23, commit `5acef5f` | Not coverage proof |
| 21 synthetic scenarios, 19 contract tests | VERIFIED | Run `./scripts/verify.sh` | Demo only |
| 4/4 confirmed synthetic writes | VERIFIED | Demo summary | Not production writes |
| 2 prompt injections blocked in demo | VERIFIED | Demo summary | Narrow regex, not a classifier |
| Model/task quality | NOT MEASURED | Private eval artifact 7/30 was all fallback | Do not cite as accuracy |
| Live PSTN latency | NOT MEASURED | Private benchmark used mock TTS, n=3 | No glass-to-glass result |
| “822 ms glass-to-glass” | FORBIDDEN — do not use | `EVALUATION.md` | Mock component benchmark only |
| Real customers, revenue or case studies | FORBIDDEN — do not use | No evidence | Design-partner conversations are not customers |
| SOC 2 / ISO 27001 / GDPR / PCI certification | FORBIDDEN — do not use | No certification evidence | Do not imply compliance |
| Complete erasure / zero PII | FORBIDDEN — do not use | Privacy audit | Erasure is partial; logs/Sheets/backups remain |
| Production-ready / autonomous operation | FORBIDDEN — do not use | Limitations | Supervised prototype only |
| Pricing/plan limits | NOT PUBLIC | Private billing catalogue | Single source is `PLAN_CATALOG`; excluded here |

## Rules

1. If a claim is not in this table, add it with evidence before publishing.
2. A demo result never proves the private product’s behaviour.
3. A private test result never proves live task quality.
4. “Implemented” does not mean “enabled” or “externally verified”.
5. When in doubt, use the weaker status.
