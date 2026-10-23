#!/usr/bin/env bash
# Run every public-repo gate: safety scan, link check, syntax, tests, demo.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== public-safety scan (including self-test)"
python3 scripts/verify-public-safety.py --self-test
python3 scripts/verify-public-safety.py

echo "== link check (including self-test)"
python3 scripts/check_links.py --self-test
python3 scripts/check_links.py

echo "== markdown check (including self-test)"
python3 scripts/check_markdown.py --self-test
python3 scripts/check_markdown.py

echo "== syntax / bytecode compile"
python3 -m compileall -q demo tests scripts

echo "== contract tests"
python3 -m unittest discover -s tests/sanitized-demo -v

echo "== scenario run"
python3 demo/simulate_call.py --all

echo "ALL PUBLIC-REPO CHECKS PASSED"
