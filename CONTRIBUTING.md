# Contributing

This is a case-study repository, not the product. Contributions that improve the
demo, docs or evidence are welcome. Contributions that add production code,
providers, credentials or customer data are not.

---

## Ground rules

1. **No real data.** Do not add names, phone numbers, emails, order IDs, transcripts,
   recordings, hostnames, account IDs or customer details — even “example” ones that
   map to a real entity.
2. **No secrets.** No keys, tokens, DSNs, private keys or `.env` files.
3. **No new dependencies.** The demo is stdlib-only on purpose. If you need a
   library, propose it in an issue first.
4. **No network calls.** The demo must run offline.
5. **No production claims.** Do not add “production-ready”, “compliant”,
   “certified”, latency numbers or customer outcomes without evidence in this repo.
6. **Tests for behaviour.** A new scenario or policy rule needs a targeted test.
7. **One concern per change.** Keep diffs small and reviewable.

---

## Development

```bash
python3 -m unittest discover -s tests/sanitized-demo -v
python3 demo/simulate_call.py --all
./scripts/verify.sh
```

`verify.sh` runs the safety scan, link check, compile check, tests and demo. A pull
request should keep it green.

---

## Adding a scenario

1. Add synthetic fixtures under `fixtures/synthetic/`.
2. Add the scenario with explicit `expect`.
3. Add or extend a test in `tests/sanitized-demo/test_safety_contract.py` if the
   scenario exercises a new rule.
4. Regenerate `assets/demo-results.json`.
5. Update [DEMO.md](DEMO.md#scenario-catalogue) if the public list changes.

Do not weaken an expectation to make a run pass. If the engine is wrong, fix the
engine; if the expectation encoded a false rule, explain why in the commit.

---

## Documentation

- Prefer short sentences and concrete evidence.
- Link to the file or command that supports a claim.
- Label synthetic, planned, partial and unverified work explicitly.
- Update [docs/claims-matrix.md](docs/claims-matrix.md) when adding a public claim.
- Run `scripts/check_links.py` after moving files.

---

## Code style

- Python 3.10+, standard library only.
- Type hints on public functions.
- `dataclasses` for state.
- No hidden global state in the engine except the deterministic caches.
- Comments explain *why*, not *what*.
- Keep the audit event vocabulary stable; tests and docs rely on it.

---

## Licence

By contributing, you agree that:

- demo code and synthetic fixtures are licensed under the MIT licence in
  [demo/LICENSE](demo/LICENSE);
- documentation and excerpts are licensed as described in [LICENSE](LICENSE);
- you have the right to submit the contribution.

Do not paste code from the private VoxFlow product or from a third party unless the
licence permits it and the source is attributed.

---

## Review checklist

- [ ] No real data or secrets.
- [ ] No network or new dependency.
- [ ] Tests pass; expectations not weakened.
- [ ] Claims match evidence.
- [ ] Links resolve.
- [ ] Licence compatible.
- [ ] Public/private distinction still clear.
