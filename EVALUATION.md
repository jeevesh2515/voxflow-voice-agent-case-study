# Evaluation

This page separates four things that are often conflated:

1. **Regression tests** — does the code still do what the suite asserts?
2. **Contract tests** — does the synthetic demo obey its stated safety rules?
3. **Model/task evaluation** — is the spoken agent accurate on real calls?
4. **Performance measurement** — how fast is a live PSTN turn?

VoxFlow has strong evidence for (1) and (2), weak evidence for (3), and **no valid
evidence for (4)**. Do not cite the numbers across categories.

---

## 1. Regression suite (private repo)

| Item | Value |
| --- | --- |
| Commit | `5acef5f` (`bulletproof-sprint`) |
| Date | 2026-10-23 |
| Command | `pytest -q` in `apps/api/` |
| Result | **963 passed, 1 skipped, 0 failed** |
| Duration | 133.29 s |
| Lint | `ruff` clean |
| Skipped test | Environment-dependent; not a hidden failure |

What this supports:

- The audited code paths load and behave as asserted.
- Identity/PIN binding, tenant isolation, grounding, Connect routing, billing and
  job-ledger tests pass together.
- The suite is broad enough to catch regressions in the exercised paths.

What it does **not** support:

- That every path is covered.
- That a passing test reflects correct product behaviour (some tests encode
  historical assumptions).
- That the system is secure, compliant, or accurate on live calls.

The full suite is not published. The public repo reproduces the **contract**, not
the private tests.

---

## 2. Demo contract tests (this repo)

```bash
python3 -m unittest discover -s tests/sanitized-demo -v
```

Result at the time of writing: **19 passed** in 0.002 s, Python 3.14, macOS.

The suite covers:

- every scenario matches its declared expectations;
- no write executes without a matching confirmation;
- a declined confirmation writes nothing;
- a duplicate write is suppressed;
- a PIN for the wrong account cannot authorise a write;
- identity is required before a read;
- unknown arguments are rejected before execution;
- malformed results are rejected;
- timeout, expiry and termination escalate;
- instruction-shaped caller speech and tool output are handled safely;
- SMS is bound to the verified caller;
- the audit trail never contains the PIN;
- the summary is computed from the runs, not hard-coded.

Run the tests after any change to `demo/` or `fixtures/`.

---

## 3. Scenario results

```bash
python3 demo/simulate_call.py --all
```

| Metric | Value |
| --- | --- |
| Scenarios | 21 |
| Resolved | 12 |
| Escalated | 9 |
| Incomplete | 0 |
| Task completion rate | 0.571 |
| Expected-outcome match | 1.0 |
| Writes executed | 4 |
| Confirmed writes | 4 |
| Confirmation compliance | 1.0 |
| Confirmations granted / declined | 7 / 1 |
| Duplicate writes suppressed | 1 |
| Injections blocked | 2 |
| Tool failures handled | 3 |
| Tool calls | 14 |

### How to read these numbers

- **Expected-outcome match 1.0 is not an accuracy score.** The fixtures and the
  engine were written together; the test asserts consistency, not generalisation.
- **9 escalations are expected outcomes**, not failures. The scenarios deliberately
  include identity failure, wrong PIN, timeout, malformed result, termination,
  prohibited refund, third-party SMS, and unknown intent.
- **Task completion 0.571** counts resolved calls only; it is not a business success
  rate.
- **Confirmation compliance 1.0** means every synthetic write had a matching
  confirmation event. It does not mean the private product has a confirmation gate.
- **Injection blocked = 2** is a regex result on two fixtures, not a security
  guarantee.

Per-scenario transcripts and audit events are in
[DEMO.md](DEMO.md#scenario-catalogue) and
[assets/trace-example.txt](assets/trace-example.txt).

---

## 4. Model and task evaluation (private)

An evaluation harness exists and can score a model against a fixture set. The last
saved artifact in the private repo scored **7/30 (23.3%)**, and every failure was a
**no-LLM fallback** (provider unavailable or misconfigured), not a model answer.

**Therefore: 23.3% must never be cited as model quality, accuracy, or task
performance.** It is an infrastructure result. It tells you the harness ran; it does
not tell you the model is bad or good.

What a credible task evaluation needs:

| Dimension | Metric | Status |
| --- | --- | --- |
| Speech recognition | WER by accent/noise band | Not measured |
| Intent routing | top-1 / top-3 accuracy | Not measured on real calls |
| Grounded answers | fact precision/recall vs source | Not measured |
| Hallucination | unbacked status rate | Lexical guard tested; no rate |
| Escalation | precision/recall vs human label | Not measured |
| Write safety | unauthorised/duplicate write rate | Demo only |
| Injection | attack success rate on a corpus | Demo only |
| Latency | p50/p95 turn latency over PSTN | Not measured |
| Cost | provider cost per resolved call | Not measured |
| Business outcome | containment, callback reduction | Not measured |

Until these exist, the honest claim is: **the harness and synthetic contract exist;
the live evaluation does not.**

---

## 5. What not to cite

<!-- safety-scan:ignore-claims-start -->
### The 822 ms benchmark

The private `BENCHMARK_REPORT.md` reports ~822 ms. Its own methodology shows:

- **n = 3** runs.
- **Mock TTS**, not audio playback.
- `AgentRunner` only, not Connect, Lex, network or telephony.
- Warm process, no queueing, no barge-in.

It is a component microbenchmark. It is **not** glass-to-glass PSTN latency and
must not appear in marketing, resumes, or buyer decks as a live number.

### The load test

`LOAD_TEST_REPORT.md` posts turns with `user_text=""`. The agent treats empty text
as silence and re-prompts. The test therefore measures the cost of a re-prompt loop,
not speech understanding or a full turn. It is **not** a voice-turn load test.

### The 23.3% evaluation

As above: all fallbacks, no model output. Not a quality score.

### The 963 tests

A regression signal, not a coverage proof, security certification, or accuracy
metric. Cite it as “963 tests passed at commit X”, not “963 tests prove safety”.

<!-- safety-scan:ignore-claims-end -->

---

## 6. Threats to validity

| Threat | Effect |
| --- | --- |
| Fixtures written with the engine | Demo expectations are tautological |
| Regex intent parser | Results do not transfer to free speech |
| No audio | No STT/TTS errors, no accent/noise effects |
| Single-process memory | No DB concurrency, retries or partial failures |
| Synthetic identifiers | No real data distribution |
| Small scenario count | Wide confidence intervals |
| Historical private run | Code may have changed since `5acef5f` |
| Environment-dependent skip | One test not exercised |

---

## 7. Reproduction

```bash
# Contract tests
python3 -m unittest discover -s tests/sanitized-demo -v

# All scenarios, human-readable
python3 demo/simulate_call.py --all

# Machine-readable results
python3 demo/simulate_call.py --all --json > /tmp/voxflow-results.json

# One scenario with transcript and audit events
python3 demo/simulate_call.py --scenario injection_in_tool_output --trace
```

The committed [assets/demo-results.json](assets/demo-results.json) is a saved run.
Regenerate it after changing the engine or fixtures:

```bash
python3 demo/simulate_call.py --all --json > assets/demo-results.json
```

---

## 8. Next evaluation milestone

Before any pilot claim, add:

1. A 100+ utterance speech set with UK accents and depot background noise.
2. Human-labelled intent and escalation ground truth.
3. A grounded-fact rubric scored against the source record.
4. A PSTN latency run with p50/p95 and a stated sample size.
5. An injection corpus with paraphrase and encoding variants.
6. A write-safety test against a staging DB, including concurrency.
7. Cost per call and per resolved call.

Until then, [LIMITATIONS.md](LIMITATIONS.md) is the accurate description.
