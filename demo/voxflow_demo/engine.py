"""Deterministic reference implementation of the VoxFlow tool-safety contract.

This is NOT the private VoxFlow product. It is a small, dependency-free model of
the *documented* contract, used so a reader can run the state machine, the
confirmation gate, the PIN binding, the idempotency guard and the
anti-hallucination rule without any provider account, audio device or network.

Everything is synthetic: accounts, orders, PINs, slots and tool results.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any


ESCALATION_SCRIPT = (
    "I can't confirm that from the live records right now. "
    "I've raised it with the operations team and someone will call you back."
)

INJECTION_RE = re.compile(
    r"ignore\s+(all\s+)?(previous|prior|your)\s+instructions"
    r"|disregard\s+(the\s+)?(rules|policy|instructions)"
    r"|you\s+are\s+now\s+"
    r"|system\s+prompt"
    r"|reveal\s+(your\s+)?(prompt|key|secret|pin)"
    r"|issue\s+(a\s+)?refund",
    re.IGNORECASE,
)

ORDER_RE = re.compile(r"\bPO-SYN-\d{4}\b", re.IGNORECASE)
SKU_RE = re.compile(r"\bSKU-[A-Z0-9-]{2,}\b", re.IGNORECASE)
SLOT_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z\b")
ACCOUNT_RE = re.compile(r"\baccount\s+([a-z0-9_]+)", re.IGNORECASE)
POSTCODE_RE = re.compile(r"\bpostcode\s+([A-Z0-9]{2,4}\s?[A-Z0-9]{2,4})\b", re.IGNORECASE)
PIN_RE = re.compile(r"\b(\d{4})\b")
LAST4_RE = re.compile(r"(?:on|number|ending)\s+(\d{4})\b", re.IGNORECASE)

STATUS_WORDS = {"delayed": "delayed", "cancelled": "cancelled", "canceled": "cancelled", "delivered": "delivered"}


class ToolFailure(Exception):
    """Base class for a refused or failed tool call."""

    code = "tool_failure"


class Refused(ToolFailure):
    code = "refused"


class SchemaError(ToolFailure):
    code = "invalid_arguments"


class ToolTimeout(ToolFailure):
    code = "tool_timeout"


class ResultRejected(ToolFailure):
    code = "invalid_tool_result"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    purpose: str
    kind: str  # read | write | external | prohibited
    requires_verified: bool = True
    requires_pin: bool = False
    requires_confirmation: bool = False
    idempotent: bool = False
    reversible: bool = True
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    result_keys: tuple[str, ...] = ()
    timeout_ms: int = 800


TOOLS: dict[str, ToolSpec] = {
    "get_order_status": ToolSpec(
        "get_order_status", "Read one order's status and ETA.", "read",
        required=("order_id",), result_keys=("order_id", "status", "eta"),
    ),
    "check_stock": ToolSpec(
        "check_stock", "Read synthetic stock for one SKU.", "read",
        required=("sku",), result_keys=("sku", "available", "units"),
    ),
    "book_delivery_slot": ToolSpec(
        "book_delivery_slot", "Book a delivery slot for an order.", "write",
        requires_confirmation=True, idempotent=True,
        required=("order_id", "slot"), result_keys=("booking_ref", "order_id", "slot"),
    ),
    "update_order_status": ToolSpec(
        "update_order_status", "Change an order status. Reversible by operations.", "write",
        requires_pin=True, requires_confirmation=True, idempotent=True,
        required=("order_id", "status"), result_keys=("order_id", "status"),
    ),
    "send_sms": ToolSpec(
        "send_sms", "Send one SMS to the verified caller's own number.", "external",
        requires_confirmation=True, idempotent=True, reversible=False,
        required=("last4", "message"), result_keys=("delivered_to_last4",),
    ),
    "escalate_to_human": ToolSpec(
        "escalate_to_human", "Open a callback for a human specialist.", "write",
        idempotent=True, required=("reason",), result_keys=("ticket",),
    ),
    "issue_refund": ToolSpec(
        "issue_refund", "Prohibited in this demo: money movement is out of scope.", "prohibited",
        reversible=False, required=("amount",),
    ),
}

WRITE_KINDS = {"write", "external"}


@dataclass
class Pending:
    tool: str
    args: dict[str, Any]
    prompt: str
    awaiting_pin: bool = False


@dataclass
class CallSession:
    call_id: str
    account: dict[str, Any]
    state: str = "greeting"
    verified: bool = False
    pin_verified: bool = False
    identity_attempts: int = 0
    pin_attempts: int = 0
    unknown_turns: int = 0
    pending: Pending | None = None
    confirmed_hash: str | None = None
    executed: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    turns: list[dict[str, str]] = field(default_factory=list)
    escalation_reason: str = ""
    expired: bool = False
    confirmation_prompts: int = 0
    outcome: str = "in_progress"

    def audit(self, event: str, **detail: Any) -> None:
        self.events.append({"event": event, "state": self.state, **detail})

    @property
    def escalated(self) -> bool:
        return bool(self.escalation_reason)


def args_hash(args: dict[str, Any]) -> str:
    blob = json.dumps(args, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _type_ok(value: Any, expected: type) -> bool:
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def validate_args(spec: ToolSpec, args: dict[str, Any]) -> None:
    if not isinstance(args, dict):
        raise SchemaError("arguments must be an object")
    allowed = set(spec.required) | set(spec.optional)
    unknown = set(args) - allowed
    if unknown:
        raise SchemaError(f"unknown argument(s): {sorted(unknown)}")
    for key in spec.required:
        if key not in args:
            raise SchemaError(f"missing required argument: {key}")
    if "order_id" in args and not ORDER_RE.fullmatch(str(args["order_id"])):
        raise SchemaError("order_id must look like PO-SYN-0000")
    if "slot" in args and not SLOT_RE.fullmatch(str(args["slot"])):
        raise SchemaError("slot must look like 2026-10-25T09:00Z")
    if "status" in args and args["status"] not in STATUS_WORDS.values():
        raise SchemaError("status not allowed by policy")
    if "amount" in args and not _type_ok(args["amount"], int):
        raise SchemaError("amount must be an integer")
    if "last4" in args and not re.fullmatch(r"\d{4}", str(args["last4"])):
        raise SchemaError("last4 must be four digits")
    if "message" in args and not str(args["message"]).strip():
        raise SchemaError("message must not be empty")


def scrub_untrusted(value: Any) -> tuple[Any, bool]:
    """Remove instruction-shaped text from tool output; never execute it."""
    removed = False
    if isinstance(value, str):
        if INJECTION_RE.search(value):
            removed = True
            return "[removed untrusted instruction]", True
        return value, False
    if isinstance(value, list):
        out = []
        for item in value:
            clean, hit = scrub_untrusted(item)
            removed = removed or hit
            out.append(clean)
        return out, removed
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            clean, hit = scrub_untrusted(item)
            removed = removed or hit
            out[key] = clean
        return out, removed
    return value, False


class ToolRuntime:
    """Executes synthetic tools behind every gate the contract requires."""

    def __init__(self, orders: dict[str, dict[str, Any]]) -> None:
        self.orders = orders
        self.bookings: dict[str, dict[str, Any]] = {}

    def _result(self, spec: ToolSpec, data: dict[str, Any]) -> dict[str, Any]:
        missing = [k for k in spec.result_keys if k not in data]
        if missing:
            raise ResultRejected(f"tool result missing {missing}")
        return {"ok": True, "data": data}

    def execute(self, session: CallSession, name: str, args: dict[str, Any]) -> dict[str, Any]:
        spec = TOOLS.get(name)
        if spec is None:
            session.audit("tool_rejected", tool=name, decision="unknown_tool")
            raise Refused("unknown tool")

        if spec.kind == "prohibited":
            session.audit("tool_blocked", tool=name, decision="prohibited")
            raise Refused("prohibited in demo")

        if session.expired:
            session.audit("tool_rejected", tool=name, decision="session_expired")
            raise Refused("session expired")

        if spec.requires_verified and not session.verified:
            session.audit("tool_rejected", tool=name, decision="identity_required")
            raise Refused("identity required")

        if spec.requires_pin and not session.pin_verified:
            session.audit("tool_rejected", tool=name, decision="pin_required")
            raise Refused("pin required")

        try:
            validate_args(spec, args)
        except SchemaError as exc:
            session.audit("tool_rejected", tool=name, decision="invalid_arguments", detail=str(exc))
            raise

        key = f"{name}:{args_hash(args)}"
        if spec.requires_confirmation and session.confirmed_hash != args_hash(args):
            session.audit("tool_blocked", tool=name, decision="confirmation_required")
            raise Refused("confirmation required")

        if spec.idempotent and key in session.executed:
            session.audit("duplicate_suppressed", tool=name, idempotency_key=key)
            cached = dict(session.executed[key])
            cached["idempotent_replay"] = True
            return cached

        session.audit("tool_request", tool=name, args_hash=args_hash(args), idempotency_key=key)

        order = self.orders.get(str(args.get("order_id", "")))
        simulate = (order or {}).get("simulate", {}).get(name)
        if simulate == "timeout":
            session.audit("tool_failure", tool=name, decision="timeout", timeout_ms=spec.timeout_ms)
            raise ToolTimeout(f"{name} timed out")
        if simulate == "terminate":
            session.audit("tool_failure", tool=name, decision="call_terminated_during_execution")
            raise Refused("call terminated during execution")
        if simulate == "malformed":
            session.audit("tool_result_rejected", tool=name, detail="upstream response missing fields")
            raise ResultRejected(f"{name} returned an incomplete record")

        if name == "get_order_status":
            if order is None or order["account_id"] != session.account["account_id"]:
                session.audit("tool_failure", tool=name, decision="not_found")
                raise Refused("order not found for this account")
            data = {"order_id": args["order_id"], "status": order["status"], "eta": order["eta"]}
            if order.get("notes"):
                data["notes"] = order["notes"]
        elif name == "check_stock":
            data = {"sku": args["sku"], "available": True, "units": 48}
        elif name == "book_delivery_slot":
            if order is None or order["account_id"] != session.account["account_id"]:
                raise Refused("order not found for this account")
            ref = "BK-" + args_hash({"o": args["order_id"], "s": args["slot"]})[:6].upper()
            self.bookings[ref] = {"order_id": args["order_id"], "slot": args["slot"]}
            data = {"booking_ref": ref, "order_id": args["order_id"], "slot": args["slot"]}
        elif name == "update_order_status":
            if order is None or order["account_id"] != session.account["account_id"]:
                raise Refused("order not found for this account")
            data = {"order_id": args["order_id"], "status": args["status"]}
        elif name == "send_sms":
            if args["last4"] != session.account["phone_last4"]:
                session.audit("tool_blocked", tool=name, decision="recipient_not_verified")
                raise Refused("recipient is not the verified caller")
            data = {"delivered_to_last4": args["last4"]}
        elif name == "escalate_to_human":
            data = {"ticket": "ESC-" + args_hash({"r": args["reason"]})[:6].upper()}
        else:  # pragma: no cover - every spec is handled above
            raise Refused("tool not implemented")

        data, removed = scrub_untrusted(data)
        if removed:
            session.audit("prompt_injection_blocked", source="tool_output", tool=name)
        try:
            result = self._result(spec, data)
        except ResultRejected as exc:
            session.audit("tool_result_rejected", tool=name, detail=str(exc))
            raise

        if spec.idempotent:
            session.executed[key] = result
        session.audit(
            "tool_result",
            tool=name,
            decision="ok",
            args_hash=args_hash(args),
            confirmed=True if spec.requires_confirmation else None,
        )
        return result


def _order_in(text: str) -> str | None:
    match = ORDER_RE.search(text)
    return match.group(0).upper() if match else None


def _is_yes(text: str) -> bool:
    return bool(re.search(r"\b(yes|yeah|yep|confirm|go ahead|please do|that's right)\b", text, re.I))


def _is_no(text: str) -> bool:
    return bool(re.search(r"\b(no|nope|don't|do not|cancel that|not now)\b", text, re.I))


class VoiceAgent:
    """Turn handler: state machine + policy gates + tool grounding."""

    def __init__(self, runtime: ToolRuntime) -> None:
        self.runtime = runtime

    def handle(self, session: CallSession, utterance: str) -> str:
        text = utterance.strip()
        session.turns.append({"role": "caller", "text": text})

        if text == "@expire":
            session.expired = True
            session.audit("session_expired")
            return self._escalate(session, "session expired before the request completed")

        if INJECTION_RE.search(text) and not (session.pending and _is_no(text)):
            session.audit("prompt_injection_blocked", source="caller_speech")
            session.state = "policy_check"
            return "I can't act on instructions like that. I can check your order, stock, or pass you to a colleague."

        if session.pending is not None:
            reply = self._resolve_pending(session, text)
            if reply is not None:
                return reply

        if not session.verified:
            return self._identity_turn(session, text)

        return self._intent_turn(session, text)

    # ---- identity -------------------------------------------------------

    def _identity_turn(self, session: CallSession, text: str) -> str:
        account_match = ACCOUNT_RE.search(text)
        postcode_match = POSTCODE_RE.search(text)
        if account_match and postcode_match:
            account_id = account_match.group(1).lower()
            postcode = re.sub(r"\s+", "", postcode_match.group(1)).upper()
            if (
                account_id == session.account["account_id"]
                and postcode == re.sub(r"\s+", "", session.account["postcode"]).upper()
            ):
                session.verified = True
                session.state = "intent_detection"
                session.audit("identity_verified", factor="account+postcode")
                return "Thank you, I've verified the account. How can I help with your order or delivery?"
            session.identity_attempts += 1
            session.audit("identity_failed", attempts=session.identity_attempts)
            if session.identity_attempts >= 2:
                return self._escalate(session, "identity verification failed twice")
            return "That doesn't match the records I have. Could you repeat the account reference and postcode?"

        session.state = "identity_check"
        return "Could you give me your account reference and the postcode on the account?"

    # ---- pending confirmation / PIN -------------------------------------

    def _resolve_pending(self, session: CallSession, text: str) -> str | None:
        pending = session.pending
        assert pending is not None

        if pending.awaiting_pin:
            match = PIN_RE.search(text)
            if not match:
                return "Please read the four-digit PIN on the account."
            if match.group(1) == session.account["pin"]:
                session.pin_verified = True
                pending.awaiting_pin = False
                session.audit("pin_verified")
                return self._ask_confirmation(session, pending)
            session.pin_attempts += 1
            session.audit("pin_failed", attempts=session.pin_attempts)
            if session.pin_attempts >= 2:
                return self._escalate(session, "PIN verification failed twice")
            return "That PIN isn't right. Please try once more."

        if _is_no(text):
            session.audit("confirmation_declined", tool=pending.tool)
            session.pending = None
            session.confirmed_hash = None
            session.state = "intent_detection"
            return "Understood, I haven't changed anything. Is there anything else?"

        if _is_yes(text):
            session.confirmed_hash = args_hash(pending.args)
            session.audit("confirmation_granted", tool=pending.tool, args_hash=session.confirmed_hash)
            session.pending = None
            session.state = "tool_execution"
            return self._run(session, pending.tool, pending.args)

        new_order = _order_in(text)
        if new_order and new_order != pending.args.get("order_id"):
            session.audit("confirmation_invalidated", tool=pending.tool, reason="order_changed")
            session.pending = None
            session.confirmed_hash = None
            session.state = "intent_detection"
            return "I've cancelled that pending request because you mentioned a different order. Which one should I action?"

        return None  # fall through: treat as a new intent, invalidating the pending action

    def _ask_confirmation(self, session: CallSession, pending: Pending) -> str:
        session.state = "tool_confirmation"
        session.confirmation_prompts += 1
        session.pending = pending
        session.confirmed_hash = None
        session.audit("confirmation_requested", tool=pending.tool, args_hash=args_hash(pending.args))
        return pending.prompt

    # ---- intents --------------------------------------------------------

    def _intent_turn(self, session: CallSession, text: str) -> str:
        lower = text.lower()

        if re.search(r"\b(human|colleague|manager|agent|person)\b", lower):
            return self._escalate(session, "caller asked for a human")

        if re.search(r"\brefund|money back\b", lower):
            session.pending = None
            session.state = "policy_check"
            try:
                self.runtime.execute(session, "issue_refund", {"amount": 100})
            except Refused:
                return "I can't process refunds on this line. I've flagged it for the finance team to review."

        if re.search(r"\b(book|slot|delivery time)\b", lower):
            order_id = _order_in(text)
            slot_match = SLOT_RE.search(text)
            if not order_id or not slot_match:
                session.unknown_turns += 1
                return "I can book a slot once I have the order reference and an ISO slot, for example 2026-10-25T09:00Z."
            pending = Pending(
                "book_delivery_slot",
                {"order_id": order_id, "slot": slot_match.group(0)},
                f"I can book {order_id} into {slot_match.group(0)}. Shall I confirm that booking?",
            )
            return self._ask_confirmation(session, pending)

        if re.search(r"\b(change|update|mark|set)\b", lower) and "status" in lower:
            order_id = _order_in(text)
            status = next((value for word, value in STATUS_WORDS.items() if word in lower), None)
            if not order_id or not status:
                session.unknown_turns += 1
                return "Which order should I update, and to which status: delayed, cancelled or delivered?"
            pending = Pending(
                "update_order_status",
                {"order_id": order_id, "status": status},
                f"To change {order_id} to {status} I need the four-digit account PIN. Please read it out.",
                awaiting_pin=True,
            )
            session.pending = pending
            session.state = "information_gathering"
            if session.pin_verified:
                pending.awaiting_pin = False
                return self._ask_confirmation(session, pending)
            return pending.prompt

        if re.search(r"\b(text|sms|message me)\b", lower):
            last4_match = LAST4_RE.search(text)
            if not last4_match:
                session.unknown_turns += 1
                return "Which number should I text? I can only message the number on the verified account."
            pending = Pending(
                "send_sms",
                {"last4": last4_match.group(1), "message": "Your VoxFlow synthetic order update is ready."},
                f"I can text the number ending {last4_match.group(1)}. Shall I send it?",
            )
            return self._ask_confirmation(session, pending)

        if re.search(r"\b(stock|available|in stock|units)\b", lower):
            sku_match = SKU_RE.search(text)
            if not sku_match:
                session.unknown_turns += 1
                return "Which SKU should I check?"
            return self._run(session, "check_stock", {"sku": sku_match.group(0).upper()})

        order_id = _order_in(text)
        if order_id:
            return self._run(session, "get_order_status", {"order_id": order_id})

        if re.search(r"\b(order|status|eta|delivery|delivered|where is|track)\b", lower):
            session.state = "information_gathering"
            return "Which purchase order should I look up? It starts with P-O-S-Y-N."

        if re.search(r"\b(bye|goodbye|that's all|nothing else|thanks)\b", lower):
            session.state = "closure"
            session.outcome = "resolved"
            session.audit("call_closed")
            return "Thank you for calling. Goodbye."

        session.unknown_turns += 1
        session.audit("intent_unrecognised", attempts=session.unknown_turns)
        if session.unknown_turns >= 2:
            return self._escalate(session, "intent not recognised twice")
        return "I can check an order, check stock, book a slot, or pass you to a colleague. Which would you like?"

    # ---- execution + grounded speech -----------------------------------

    def _run(self, session: CallSession, name: str, args: dict[str, Any]) -> str:
        session.state = "tool_execution"
        try:
            result = self.runtime.execute(session, name, args)
        except ToolFailure:
            return self._escalate(session, f"{name} did not return a usable result")

        session.state = "result_validation"
        data = result["data"]
        if name == "get_order_status":
            reply = (
                f"Order {data['order_id']} is {data['status']}. "
                f"The latest ETA in the records is {data['eta']}."
            )
        elif name == "check_stock":
            reply = f"{data['sku']} has {data['units']} units available."
        elif name == "book_delivery_slot":
            reply = f"Booked. The reference is {data['booking_ref']} for {data['slot']}."
        elif name == "update_order_status":
            reply = f"Updated {data['order_id']} to {data['status']} in the records."
        elif name == "send_sms":
            reply = f"Sent to the verified number ending {data['delivered_to_last4']}."
        else:  # pragma: no cover
            reply = ESCALATION_SCRIPT

        if result.get("idempotent_replay"):
            reply = "That request was already completed, so I haven't repeated it. " + reply
        session.state = "closure"
        session.outcome = "resolved"
        return reply

    def _escalate(self, session: CallSession, reason: str) -> str:
        session.escalation_reason = reason
        session.state = "human_escalation"
        session.outcome = "escalated"
        session.audit("escalated", reason=reason)
        return ESCALATION_SCRIPT
