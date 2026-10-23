# Code walkthrough

Short, sanitized excerpts from the private repository, chosen because the technique
is the case study. They are **abridged and not runnable**. Private prompts, schemas,
provider configuration and customer logic are excluded.

Read these with [TOOL-SAFETY.md](../TOOL-SAFETY.md) and
[LIMITATIONS.md](../LIMITATIONS.md): the excerpts show what is implemented, and the
limitations page says what is not.

| # | Excerpt | Technique | Private product status |
| --- | --- | --- | --- |
| 01 | [PIN storage and supplier binding](01-pin-binding.md) | PBKDF2, constant-time verify, factor-to-supplier binding | Implemented and tested |
| 02 | [Grounded speech](02-grounded-speech.md) | Allow-listed tool facts + lexical unbacked-status guard | Implemented; lexical only |
| 03 | [Tool gating and tenant scoping](03-tool-gating.md) | Session authorisation, supplier binding, explicit `tenant_id` | Implemented; confirmation/schema missing |
| 04 | [Signed Connect bridge](04-signed-connect-bridge.md) | HMAC-SHA256, freshness window, replay ledger | Implemented and tested |

## What is deliberately not shown

- System prompts and prompt-building logic.
- Full tool definitions, argument schemas and result schemas.
- Database schema and migrations.
- Provider adapters and credentials.
- Billing catalogue and price identifiers.
- Customer-specific routing, sheets, prompts or data.
- Deployment manifests, Terraform state, hostnames or account IDs.

The excerpts are enough to evaluate the engineering approach. They are not enough to
clone the product, and that is intentional.

## Source and licence

Source: private VoxFlow repository, branch `bulletproof-sprint`, commit `5acef5f`,
audited 2026-10-23. Excerpts are proprietary; see [../LICENSE](../LICENSE). Viewing
and evaluation are permitted; copying into a competing product is not.
