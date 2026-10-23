# Excerpt 02 — Grounded speech

**Source:** private VoxFlow repository, commit `5acef5f`, files
`agent/tools.py` and `agent/runner.py`. Abridged.
**Why it is safe:** shows the grounding policy, not prompts, schemas or customer data.

---

## The failure being prevented

A caller asks, “Has my order been dispatched?” The status tool times out. A fluent
model may still answer:

> “Yes, it was dispatched yesterday and should arrive tomorrow.”

That sentence is worse than a transfer. VoxFlow’s rule is: **if the tool did not
successfully return the fact, the agent does not say it.**

---

## Layer 1 — classify the tool result

```python
STATUS_ESCALATE_SCRIPT = (
    "I can't confirm that from the live records right now. "
    "I've raised it with our operations team — someone will call you back."
)

_STATUS_FACT_FIELDS = (
    "status", "po_signed", "total_qty", "qty_ordered", "eta", "dispatch_date",
    "dispatched_at", "expected_delivery", "total", "available", "appointment_id",
)


def speak_from_tool(result: Any) -> dict[str, Any]:
    """Classify one tool result for spoken delivery. {ok, speak, escalate}."""
    if isinstance(result, dict):
        escalate = (
            result.get("ok") is False
            or bool(result.get("error"))
            or result.get("found") is False
            or ("available" in result and "total" not in result and not result.get("reason"))
        )
        if not escalate:
            facts = [
                f"{k}: {result[k]}"
                for k in _STATUS_FACT_FIELDS
                if result.get(k) not in (None, "", [], {})
            ]
            if facts:
                return {"ok": True, "speak": ", ".join(facts), "escalate": False}
    return {"ok": False, "speak": STATUS_ESCALATE_SCRIPT, "escalate": True}
```

**What this buys:** speech is built from a fixed field list, not from free-form model
prose. Errors, not-found results and empty records all collapse to the escalation
script.

**What it does not buy:** the field list can be incomplete, and the values themselves
are trusted once returned. A bad upstream row produces a confidently spoken bad fact.
Schema validation of results is the missing complement.

---

## Layer 2 — block unbacked status prose

The model can also volunteer status in a sentence that never called `speak_from_tool`.
A second guard inspects the final reply and asks whether a status tool actually
succeeded.

```python
_UNBACKED_STATUS_RE = re.compile(
    r"\b(?:loaded|in[- ]stock|out[- ]of[- ]stock|eta|units?|pallets?|dispatched|"
    r"in transit|delivered|dock|bay)\b",
    re.IGNORECASE,
)

STATUS_TOOL_NAMES = {
    "check_po_status", "get_order_details", "fetch_po_from_sheet",
    "get_shipment_status", "check_stock",
}
```

```python
# 4. Status-bearing reply with no successful status tool result -> escalate.
if _UNBACKED_STATUS_RE.search(reply):
    backed = False
    for act in actions:
        if act.get("name") not in STATUS_TOOL_NAMES:
            continue
        res = act.get("result")
        if (
            isinstance(res, dict)
            and res.get("ok") is not False
            and not res.get("error")
            and res.get("found") is not False
        ):
            backed = True
            break
    if not backed:
        if session is not None:
            session.reason = "unbacked_status_guarded"
        return STATUS_ESCALATE_SCRIPT
```

The same function also:

- strips reasoning/tool markup before speech;
- catches a status claim after a not-found order lookup;
- replaces unknown SKU tokens with “the requested item”;
- rewrites “I’ve updated the sheet” when the write failed or is only queued;
- caps spoken output at two sentences.

---

## Why a lexical guard is honest — and limited

It is honest because it is described as a heuristic. The code comment says so:

```python
# ponytail: lexical word list, not NLP; extend when new status vocabulary appears.
```

It catches the common failure mode (the model says “dispatched” without a dispatch
fact). It does not catch:

- a paraphrase (“it left us on Tuesday”);
- a numeric inconsistency (ETA in the past, quantity above order size);
- a false claim that contains none of the trigger words;
- a malicious tool result with a plausible status.

A semantic entailment check or a structured “fact ledger” would be stronger. That is
future work, not a current capability.

---

## What the demo does

The demo goes further than the private product: it builds speech only from a
validated result object and rejects missing keys before speech. It does not use an
LLM, so there is no free-form prose to guard. That makes the demo’s grounding
**stronger** than production for its narrow path — another reason the demo is not a
parity test.

Tests: `test_tool_timeout_escalates_without_inventing_status`,
`test_malformed_tool_result_is_rejected`.
