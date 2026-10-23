#!/usr/bin/env bash
# Convenience wrapper for the synthetic simulator.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 demo/simulate_call.py "$@"
