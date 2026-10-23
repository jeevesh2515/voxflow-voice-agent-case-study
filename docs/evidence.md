# Evidence log

Snapshot date: **2026-10-23**
Environment: macOS, Python **3.14.5**, no third-party Python packages.
Working tree: public staging only. No remote, no push, no visibility change.

This page records what was actually run, what it returned, and what it does not
prove. It exists so a reviewer can separate reproducible checks from private
snapshots and from claims that remain unmeasured.

---

## 1. Reproducible checks

Run everything with:

```bash
./scripts/verify.sh
```

The gate runs the safety scan, link check, markdown check, Python compilation,
contract tests and all synthetic scenarios. Last result:

```text
PUBLIC-SAFETY SCAN PASSED: no secrets, private identifiers or unsupported claims found.
LINK CHECK PASSED: all relative links and anchors resolve.
MARKDOWN CHECK PASSED: fences, headings and whitespace are clean.
...
Ran 19 tests in 0.002s
OK
...
ALL PUBLIC-REPO CHECKS PASSED
```

### Individual commands

| Check | Command | Result |
| --- | --- | --- |
| Safety scan | `python3 scripts/verify-public-safety.py` | PASSED |
| Safety self-test | `python3 scripts/verify-public-safety.py --self-test` | `self-test: 9 cases passed` |
| Link check | `python3 scripts/check_links.py` | PASSED |
| Link self-test | `python3 scripts/check_links.py --self-test` | `self-test: 2 expected problems detected` |
| Markdown check | `python3 scripts/check_markdown.py` | PASSED |
| Markdown self-test | `python3 scripts/check_markdown.py --self-test` | `self-test: 6 expected problems detected` |
| Compile | `python3 -m compileall -q demo tests scripts` | exit 0 |
| Contract tests | `python3 -m unittest discover -s tests/sanitized-demo` | `Ran 19 tests`, `OK` |
| Demo | `python3 demo/simulate_call.py --all` | 21 scenarios, 0 incomplete |
| History secret scan | `gitleaks detect --source . --redact` | 1 commit, no leaks |
| Tree secret scan | `gitleaks dir . --redact` | no leaks |

### Demo summary (exact output)

```text
scenarios: 21
resolved: 12
escalated: 9
incomplete: 0
task_completion_rate: 0.571
expected_outcome_match_rate: 1.0
writes_executed: 4
confirmed_writes: 4
confirmation_compliance: 1.0
confirmations_declined: 1
confirmations_granted: 7
duplicates_suppressed: 1
injections_blocked: 2
tool_failures: 3
tool_calls: 14
```

Saved artefact: [`assets/demo-results.json`](../assets/demo-results.json).
Human-readable trace: [`assets/trace-example.txt`](../assets/trace-example.txt).

### Tree checks

| Item | Value |
| --- | --- |
| Files (excluding generated `__pycache__`) | 51 |
| Total size | 1.7 MB |
| Audio / video / image / PDF files | 0 |
| `.env` files | 0 (only audited `.env.example`) |
| Third-party Python dependencies | 0 |

---

## 2. Private snapshot (not reproducible here)

The private product is not published. The following result is a dated snapshot,
reported so the public claim is traceable, not so it can be re-run from this
repository.

| Item | Value |
| --- | --- |
| Private commit | `5acef5f` |
| Date | 2026-10-23 |
| Command | `pytest -q` in the API package |
| Result | **963 passed, 1 skipped, 0 failed** |
| Duration | 133.29 s |
| Lint | `ruff` clean |
| Skipped test | Environment-dependent; not a hidden failure |

What it supports: the audited code paths load and behave as asserted, and the
suite catches regressions in those paths.

What it does not support: coverage, security, compliance, or task accuracy. A
green regression suite is not a product-quality measurement. See
[EVALUATION.md](../EVALUATION.md).

---

## 3. What was not run

| Not run | Why it matters |
| --- | --- |
| PSTN call to a real number | No public number, no carrier access, no consent |
| Real STT / LLM / TTS providers | No keys in public staging; results would not be reproducible |
| Audio playback or barge-in test | The demo has no audio path |
| Concurrent database writes | The demo is a single-process state machine |
| Load or latency measurement | No valid sample; see [EVALUATION.md](../EVALUATION.md) |
| External penetration test | Out of scope; the threat model is a design document |

The synthetic demo does not exercise a real provider, a real database, a real
telephone network or a real caller. Its numbers describe the demo contract only.

---

## 4. History and publication state

At the time of this log:

- a local repository exists on `main` with one commit;
- there is no remote, no push, no release and no visibility change;
- the commit author is a placeholder name with a reserved `.example` address,
  not the owner's personal identity;
- the private repository remains private and unchanged in visibility.

`gitleaks` 8.30.1 scanned the working tree and the single-commit history:

```text
1 commits scanned.
scanned ~1.67 MB
no leaks found
```

Before any publication:

1. The owner sets the final commit author identity and confirms the commit.
2. Re-run `gitleaks detect --source . --redact` and `./scripts/verify.sh`.
3. If anything private appears in history, delete the repository and recreate it
   from the clean tree. Do not rewrite history and assume the material is gone.
4. Obtain explicit owner approval for the repository name, contents, licence and
   visibility.

---

## 5. Interpretation rules

1. A demo result never proves the private product's behaviour.
2. A private test result never proves task quality, safety or compliance.
3. "Implemented" does not mean "enabled", "deployed" or "externally verified".
4. Absence of a finding in the safety scan is not proof of absence; it is one
   heuristic gate plus human review.
5. When evidence is missing, the correct status is **not measured**, not an
   estimate.
