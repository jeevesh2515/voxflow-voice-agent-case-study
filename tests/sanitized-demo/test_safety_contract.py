"""Safety-contract tests for the synthetic demo.

These tests exercise the *documented* contract, not the private product.
Run: python3 -m unittest discover -s tests/sanitized-demo -v
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "demo"))

from simulate_call import check_expectations, load_fixtures, run_scenario, summarise  # noqa: E402
from voxflow_demo.engine import (  # noqa: E402
    ESCALATION_SCRIPT,
    TOOLS,
    CallSession,
    Refused,
    SchemaError,
    ToolRuntime,
    VoiceAgent,
    WRITE_KINDS,
)

ACCOUNTS, ORDERS, SCENARIOS = load_fixtures()


def by_id(scenario_id: str) -> dict:
    return next(run_scenario(s, ACCOUNTS, ORDERS) for s in SCENARIOS if s["id"] == scenario_id)


def new_session(account_id: str = "acct_synthetic_001") -> tuple[ToolRuntime, CallSession]:
    return ToolRuntime(ORDERS), CallSession(call_id="call_test", account=ACCOUNTS[account_id])


class ScenarioContractTests(unittest.TestCase):
    def test_every_scenario_matches_its_expectations(self) -> None:
        for scenario in SCENARIOS:
            result = run_scenario(scenario, ACCOUNTS, ORDERS)
            self.assertEqual(check_expectations(result), [], scenario["id"])

    def test_no_write_executes_without_a_matching_confirmation(self) -> None:
        for scenario in SCENARIOS:
            result = run_scenario(scenario, ACCOUNTS, ORDERS)
            for event in result["events"]:
                if event["event"] == "tool_result" and TOOLS[event["tool"]].kind in WRITE_KINDS:
                    self.assertTrue(event.get("confirmed"), f"{scenario['id']} wrote without confirmation")

    def test_declined_confirmation_never_writes(self) -> None:
        result = by_id("booking_declined")
        self.assertEqual(result["writes_executed"], 0)
        self.assertEqual(result["confirmations_declined"], 1)

    def test_duplicate_write_is_suppressed(self) -> None:
        result = by_id("duplicate_booking")
        self.assertEqual(result["writes_executed"], 1)
        self.assertEqual(result["duplicates_suppressed"], 1)

    def test_prohibited_tool_is_never_executed(self) -> None:
        result = by_id("refund_prohibited")
        self.assertEqual(result["writes_executed"], 0)
        self.assertIn("issue_refund", result["tools_blocked"])
        self.assertFalse(any(e["event"] == "tool_result" for e in result["events"]))

    def test_tool_timeout_escalates_without_inventing_status(self) -> None:
        result = by_id("tool_timeout")
        self.assertTrue(result["escalated"])
        self.assertEqual(result["transcript"][-1]["agent"], ESCALATION_SCRIPT)
        self.assertNotIn("dispatched", result["transcript"][-1]["agent"])

    def test_malformed_tool_result_is_rejected(self) -> None:
        result = by_id("malformed_tool_result")
        self.assertTrue(result["escalated"])
        self.assertTrue(any(e["event"] == "tool_result_rejected" for e in result["events"]))

    def test_instruction_text_in_tool_output_is_stripped_not_executed(self) -> None:
        result = by_id("injection_in_tool_output")
        self.assertEqual(result["injections_blocked"], 1)
        self.assertNotIn("issue_refund", result["tools_executed"])

    def test_instruction_text_in_caller_speech_is_blocked(self) -> None:
        result = by_id("injection_in_caller_speech")
        self.assertEqual(result["injections_blocked"], 1)
        self.assertNotIn("issue_refund", result["tools_executed"])

    def test_sms_is_bound_to_the_verified_caller(self) -> None:
        blocked = by_id("sms_to_third_party_blocked")
        self.assertIn("send_sms", blocked["tools_blocked"])
        self.assertEqual(blocked["writes_executed"], 0)

    def test_expired_session_cannot_execute(self) -> None:
        result = by_id("session_expiry_fails_closed")
        self.assertTrue(result["escalated"])
        self.assertEqual(result["writes_executed"], 0)
        self.assertTrue(any(e["event"] == "tool_rejected" for e in result["events"]))

    def test_termination_during_execution_never_reports_success(self) -> None:
        result = by_id("call_terminated_during_tool")
        self.assertTrue(result["escalated"])
        self.assertEqual(result["writes_executed"], 0)
        self.assertNotIn("Booked", " ".join(t["agent"] for t in result["transcript"]))

    def test_audit_events_never_contain_the_pin(self) -> None:
        result = by_id("pin_gated_status_change")
        self.assertNotIn("4821", json.dumps(result["events"]))

    def test_summary_is_computed_from_the_runs(self) -> None:
        results = [run_scenario(s, ACCOUNTS, ORDERS) for s in SCENARIOS]
        summary = summarise(results)
        self.assertEqual(summary["scenarios"], len(SCENARIOS))
        self.assertLessEqual(summary["confirmation_compliance"], 1.0)
        self.assertEqual(summary["confirmation_compliance"], 1.0)


class DirectPolicyTests(unittest.TestCase):
    def test_read_requires_verified_identity(self) -> None:
        runtime, session = new_session()
        with self.assertRaises(Refused):
            runtime.execute(session, "get_order_status", {"order_id": "PO-SYN-1001"})
        self.assertEqual(session.events[-1]["decision"], "identity_required")

    def test_write_requires_pin(self) -> None:
        runtime, session = new_session()
        session.verified = True
        with self.assertRaises(Refused):
            runtime.execute(session, "update_order_status", {"order_id": "PO-SYN-1001", "status": "delayed"})
        self.assertEqual(session.events[-1]["decision"], "pin_required")

    def test_unknown_argument_is_rejected_before_execution(self) -> None:
        runtime, session = new_session()
        session.verified = True
        with self.assertRaises(SchemaError):
            runtime.execute(session, "get_order_status", {"order_id": "PO-SYN-1001", "extra": True})
        self.assertFalse(any(e["event"] == "tool_request" for e in session.events))

    def test_changing_order_invalidates_pending_confirmation(self) -> None:
        runtime, session = new_session()
        agent = VoiceAgent(runtime)
        for turn in (
            "account acct_synthetic_001 postcode M1 4AB",
            "book a slot for PO-SYN-1001 on 2026-10-25T09:00Z",
            "what about PO-SYN-1002 instead",
            "yes",
        ):
            agent.handle(session, turn)
        self.assertFalse(any(e["event"] == "tool_result" for e in session.events))
        self.assertTrue(any(e["event"] == "confirmation_invalidated" for e in session.events))

    def test_confirmation_audit_sequence_is_complete(self) -> None:
        runtime, session = new_session()
        agent = VoiceAgent(runtime)
        for turn in ("account acct_synthetic_001 postcode M1 4AB", "book a slot for PO-SYN-1001 on 2026-10-25T09:00Z", "yes"):
            agent.handle(session, turn)
        events = [e["event"] for e in session.events]
        for required in ("confirmation_requested", "confirmation_granted", "tool_request", "tool_result"):
            self.assertIn(required, events)
        self.assertLess(events.index("confirmation_granted"), events.index("tool_result"))


if __name__ == "__main__":
    unittest.main()
