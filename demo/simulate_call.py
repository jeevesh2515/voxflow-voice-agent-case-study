#!/usr/bin/env python3
"""Run the synthetic VoxFlow policy simulator.

Deterministic, offline, stdlib-only. No provider keys, no network, no audio,
no real accounts. Every identifier is synthetic.

    python3 demo/simulate_call.py --list
    python3 demo/simulate_call.py --scenario normal_order_status --trace
    python3 demo/simulate_call.py --all --json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from voxflow_demo.engine import TOOLS, CallSession, ToolRuntime, VoiceAgent, WRITE_KINDS  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "synthetic"


def load_fixtures() -> tuple[dict[str, dict], dict[str, dict], list[dict]]:
    accounts = {a["account_id"]: a for a in json.loads((FIXTURES / "accounts.json").read_text())["accounts"]}
    orders = json.loads((FIXTURES / "accounts.json").read_text())["orders"]
    scenarios = json.loads((FIXTURES / "scenarios.json").read_text())["scenarios"]
    return accounts, orders, scenarios


def run_scenario(scenario: dict, accounts: dict[str, dict], orders: dict[str, dict]) -> dict:
    runtime = ToolRuntime(orders)
    agent = VoiceAgent(runtime)
    session = CallSession(call_id=f"call_{scenario['id']}", account=accounts[scenario["account_id"]])
    transcript = []
    for turn in scenario["turns"]:
        reply = agent.handle(session, turn)
        transcript.append({"caller": turn, "agent": reply})
    if session.outcome == "in_progress":
        session.outcome = "incomplete"

    executed = {
        e["tool"] for e in session.events if e["event"] in ("tool_request", "tool_result")
    }
    blocked = {e["tool"] for e in session.events if e["event"] == "tool_blocked"}
    writes = {
        e["tool"]
        for e in session.events
        if e["event"] == "tool_result" and TOOLS[e["tool"]].kind in WRITE_KINDS
    }
    result = {
        "scenario": scenario["id"],
        "title": scenario["title"],
        "outcome": session.outcome,
        "escalated": session.escalated,
        "escalation_reason": session.escalation_reason,
        "tools_executed": sorted(executed),
        "tools_blocked": sorted(blocked),
        "writes_executed": len(writes),
        "confirmations_requested": session.confirmation_prompts,
        "confirmations_declined": sum(1 for e in session.events if e["event"] == "confirmation_declined"),
        "confirmation_grants": sum(1 for e in session.events if e["event"] == "confirmation_granted"),
        "duplicates_suppressed": sum(1 for e in session.events if e["event"] == "duplicate_suppressed"),
        "injections_blocked": sum(1 for e in session.events if e["event"] == "prompt_injection_blocked"),
        "tool_failures": sum(1 for e in session.events if e["event"] in ("tool_failure", "tool_result_rejected")),
        "turns": len(scenario["turns"]),
        "transcript": transcript,
        "events": session.events,
        "expect": scenario.get("expect", {}),
    }
    return result


def check_expectations(result: dict) -> list[str]:
    expect = result["expect"]
    problems: list[str] = []
    if expect.get("outcome") and result["outcome"] != expect["outcome"]:
        problems.append(f"outcome {result['outcome']} != {expect['outcome']}")
    if expect.get("tools") is not None and result["tools_executed"] != sorted(expect["tools"]):
        problems.append(f"tools {result['tools_executed']} != {expect['tools']}")
    if expect.get("writes") is not None and result["writes_executed"] != expect["writes"]:
        problems.append(f"writes {result['writes_executed']} != {expect['writes']}")
    if expect.get("escalated") is not None and result["escalated"] != expect["escalated"]:
        problems.append(f"escalated {result['escalated']} != {expect['escalated']}")
    if expect.get("confirmations") is not None and result["confirmations_requested"] != expect["confirmations"]:
        problems.append(f"confirmations {result['confirmations_requested']} != {expect['confirmations']}")
    if expect.get("duplicates") is not None and result["duplicates_suppressed"] != expect["duplicates"]:
        problems.append(f"duplicates {result['duplicates_suppressed']} != {expect['duplicates']}")
    if expect.get("injections") is not None and result["injections_blocked"] != expect["injections"]:
        problems.append(f"injections {result['injections_blocked']} != {expect['injections']}")
    if expect.get("blocked") is not None and len(result["tools_blocked"]) != expect["blocked"]:
        problems.append(f"blocked {len(result['tools_blocked'])} != {expect['blocked']}")
    return problems


def summarise(results: list[dict]) -> dict:
    total = len(results)
    writes_executed = sum(result["writes_executed"] for result in results)
    confirmed_writes = sum(
        1
        for result in results
        for event in result["events"]
        if event["event"] == "tool_result"
        and event.get("confirmed")
        and TOOLS[event["tool"]].kind in WRITE_KINDS
    )
    return {
        "scenarios": total,
        "resolved": sum(1 for r in results if r["outcome"] == "resolved"),
        "escalated": sum(1 for r in results if r["outcome"] == "escalated"),
        "incomplete": sum(1 for r in results if r["outcome"] == "incomplete"),
        "task_completion_rate": round(sum(1 for r in results if r["outcome"] == "resolved") / total, 3),
        "expected_outcome_match_rate": round(
            sum(1 for r in results if r["outcome"] == r["expect"].get("outcome")) / total, 3
        ),
        "writes_executed": writes_executed,
        "confirmed_writes": confirmed_writes,
        "confirmation_compliance": round(confirmed_writes / writes_executed, 3) if writes_executed else 1.0,
        "confirmations_declined": sum(r["confirmations_declined"] for r in results),
        "confirmations_granted": sum(r["confirmation_grants"] for r in results),
        "duplicates_suppressed": sum(r["duplicates_suppressed"] for r in results),
        "injections_blocked": sum(r["injections_blocked"] for r in results),
        "tool_failures": sum(r["tool_failures"] for r in results),
        "tool_calls": sum(len(r["tools_executed"]) for r in results),
        "escalation_precision_note": "every escalation in these fixtures is expected; see EVALUATION.md",
    }


def print_run(result: dict, trace: bool) -> None:
    print(f"\n=== {result['scenario']}: {result['title']}")
    print(f"    outcome={result['outcome']} escalated={result['escalated']} "
          f"tools={result['tools_executed']} blocked={result['tools_blocked']}")
    if trace:
        for turn in result["transcript"]:
            print(f"    caller: {turn['caller']}")
            print(f"    agent : {turn['agent']}")
        print("    audit events:")
        for event in result["events"]:
            print("      " + json.dumps(event, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="scenario id to run")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--list", action="store_true", help="list scenario ids")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument("--trace", action="store_true", help="print the synthetic transcript and audit events")
    args = parser.parse_args()

    accounts, orders, scenarios = load_fixtures()

    if args.list:
        for scenario in scenarios:
            print(f"{scenario['id']:<32} {scenario['title']}")
        return 0

    selected = scenarios if args.all or not args.scenario else [s for s in scenarios if s["id"] == args.scenario]
    if not selected:
        print(f"unknown scenario: {args.scenario}", file=sys.stderr)
        return 2

    results = [run_scenario(s, accounts, orders) for s in selected]
    failures = {r["scenario"]: check_expectations(r) for r in results}
    failures = {k: v for k, v in failures.items() if v}

    if args.json:
        print(json.dumps({"results": results, "summary": summarise(results), "expectation_failures": failures}, indent=2))
    else:
        for result in results:
            print_run(result, args.trace)
        summary = summarise(results)
        print("\n--- summary")
        for key, value in summary.items():
            print(f"    {key}: {value}")
        if failures:
            print("\n!!! expectation failures")
            for scenario, problems in failures.items():
                print(f"    {scenario}: {'; '.join(problems)}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
