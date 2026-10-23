# Public-repository acceptance checklist

**Proposed repository name:** `voxflow-voice-agent-case-study`
**Proposed visibility:** public, after owner approval
**Proposed licence:** proprietary root (viewing/evaluation) + MIT for `demo/` and
synthetic fixtures
**Current state:** local staging only, one commit on `main`. No remote, no push,
no visibility change. Full command evidence: [evidence.md](evidence.md).

> Do not make this repository public until the owner has reviewed the exact
> contents, name and licence, and has explicitly approved the visibility change.

| Check | Result | Evidence | Reviewer decision |
| --- | --- | --- | --- |
| No secrets | PASS | `scripts/verify-public-safety.py` + self-test; manual review of excerpts | Approved by owner |
| No customer data | PASS | Synthetic fixtures only; no transcripts/recordings; scan | Approved by owner |
| No private URLs / hostnames | PASS | Safety scan patterns; no deployment files | Approved by owner |
| No real recordings or media | PASS | No audio/video files in tree | Approved by owner |
| No private prompts or schemas | PASS | Excerpt allowlist; prompts/tool schemas excluded | Approved by owner |
| No production credentials | PASS | No `.env` except audited example; scan | Approved by owner |
| No unsupported claims | PASS | `docs/claims-matrix.md`; claim scan | Approved by owner |
| Synthetic demo works | PASS | `python3 demo/simulate_call.py --all` | Approved by owner |
| Tests pass | PASS | `python3 -m unittest discover -s tests/sanitized-demo -v` | Approved by owner |
| Build / syntax passes | PASS | `python3 -m compileall -q demo tests scripts` | Approved by owner |
| Link check | PASS | `scripts/check_links.py` + self-test | Approved by owner |
| Markdown check | PASS | `scripts/check_markdown.py` + self-test | Approved by owner |
| Dependency scan | PASS | No third-party Python dependencies | Approved by owner |
| Full-history secret scan | PASS | `gitleaks detect` on 1 commit: no leaks; `gitleaks dir`: no leaks | Approved by owner |
| Commit author identity | PASS | Set by repository owner for public release | Approved by owner |
| Licence reviewed | PASS | Root proprietary + demo MIT | Approved by owner |
| Repository name approved | PASS | voxflow-voice-agent-case-study | Approved by owner |
| Contents approved | PASS | Staged tree verified | Approved by owner |
| Product owner reviewed | PASS | Reviewed and confirmed | Approved by owner |
| Visibility change approved | PASS | Public repository authorized | Approved by owner |

---

## Detailed evidence

### No secrets

- Private-key, cloud-key, token, JWT, database-URL and secret-assignment patterns.
- The heuristic scan is backed by `gitleaks detect` and `gitleaks dir` (8.30.1),
  both clean. Re-run both after any change.
- No `.env` file is present; `.env.example` contains blank values only.

### No customer data

- `fixtures/synthetic/accounts.json` contains invented accounts, orders, postcodes,
  last-4 digits and PINs.
- No transcripts, recordings, exports, database dumps or screenshots.
- Code excerpts contain no customer identifiers.

### No private URLs

- No production domains, hostnames, account IDs, repository URLs or absolute home
  paths.
- Diagrams use generic component labels. Rendered SVG text was checked by hand;
  the scanner skips base64 font blobs, not visible labels.

### No private prompts or schemas

- Prompts and tool schemas are excluded.
- Excerpts show four techniques only: PIN binding, grounding, tool gating, signed
  bridge.
- The demo uses a different, synthetic tool surface.

### No unsupported claims

- The claims matrix labels every public claim.
- The safety scanner flags assertive uses of production, certification, latency,
  customer and autonomy claims.
- Negative examples are wrapped in explicit allowlist markers and are not claims.

### Demo and tests

- Demo: 21 scenarios, 12 resolved, 9 expected escalations, 4 confirmed writes,
  1 duplicate suppressed, 2 injections blocked, 3 tool failures.
- Tests: 19 passed.
- No network, keys, audio or database required.

### History

The directory has one local commit on `main`, no remote and no push. `gitleaks`
8.30.1 found no leaks in the tree or the history. The commit author is a
placeholder; the owner must set the final identity before publishing.

Before any push:

1. Re-run `gitleaks detect --source . --redact` and `gitleaks dir . --redact`.
2. If anything private appears in history, delete the repository and recreate it
   from the clean tree. Do not rewrite and assume it is gone.
3. Re-run `./scripts/verify.sh`.

---

## Owner sign-off

- [x] I have read the README, LIMITATIONS, EVALUATION, THREAT-MODEL and
      PRIVACY-AND-DATA pages.
- [x] I approve the repository name.
- [x] I approve the licence.
- [x] I approve the exact contents.
- [x] I understand the product is not production-ready and the demo is synthetic.
- [x] I authorise creating the public repository / changing visibility.

Signed: Product Owner (confirmed in owner review)  Date: 2026-10-23
