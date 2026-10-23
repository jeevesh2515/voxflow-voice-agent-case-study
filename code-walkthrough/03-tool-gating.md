# Excerpt 03 — Tool gating and tenant scoping

**Source:** private VoxFlow repository, commit `5acef5f`,
`agent/tools.py`. Abridged.
**Why it is safe:** shows authorisation shape and query scoping, not schemas or data.

---

## The rule

A tool is not allowed because the model selected it. It is allowed because the
session carries the right factors, bound to the right supplier, and the query is
scoped to the right tenant.

---

## Read gate

```python
def _knowledge_authorized_supplier_id(session: CallSession) -> str | None:
    supplier_id = session.supplier_id
    if (
        supplier_id
        and session.verified
        and _bound_supplier_id(session, _KNOWLEDGE_BINDING_KEY) == supplier_id
    ):
        return supplier_id
    return None


def _sensitive_read_denial(session: CallSession) -> dict[str, Any] | None:
    """Require authorization factors bound to the currently identified contact."""
    supplier_id = _knowledge_authorized_supplier_id(session)
    if supplier_id is None:
        return {
            "ok": False,
            "error": "not_verified",
            "message": "Verify the caller before sharing order data.",
        }
    if (
        session.verification_mode == "enhanced"
        and _pin_authorized_supplier_id(session) != supplier_id
    ):
        return {
            "ok": False,
            "error": "pin_required",
            "message": "Enhanced verification requires a valid PIN before sharing order data.",
        }
    return None
```

Every sensitive read calls the gate before touching the database:

```python
async def get_shipment_status(session, order_id=None, supplier_phone=None):
    if denial := _sensitive_read_denial(session):
        return denial
    ...
    supplier_id = _knowledge_authorized_supplier_id(session)
    async with async_session_scope() as db:
        q = (
            select(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .where(
                Shipment.tenant_id == session.tenant_id,
                Order.tenant_id == session.tenant_id,
                Order.supplier_id == supplier_id,
            )
        )
        ...
```

**Three predicates matter:** `Shipment.tenant_id`, `Order.tenant_id` and
`Order.supplier_id`. The first prevents cross-tenant reads; the third prevents a
verified caller from reading another supplier’s order inside the same tenant.

**Limits**

- The gate must be called by every new read. Nothing enforces that at the type level.
- `_sensitive_read_denial` returns a denial dict but does not log every denial, so
  probing can be invisible.
- Some reads are intentionally less restricted (for example, call-outcome audit).

---

## Write gate

High-impact writes use the PIN binding directly:

```python
async def create_po(session, supplier_id=None, items=None, notes=""):
    authorized_supplier_id = _pin_authorized_supplier_id(session)
    if authorized_supplier_id is None:
        log.warning("security.tier2_blocked", ...)
        return {"ok": False, "error": "pin_required", ...}

    if not supplier_id:
        supplier_id = authorized_supplier_id
    if supplier_id != authorized_supplier_id:
        return {"ok": False, "error": "supplier_mismatch", ...}
    ...
```

Other writes use a knowledge binding:

```python
async def schedule_appointment(session, ...):
    if _knowledge_authorized_supplier_id(session) is None:
        return {"ok": False, "error": "not_verified", ...}
    ...
```

**Limits**

- The model supplies the arguments. There is no shared schema check for required
  keys, unknown keys, formats or ranges.
- There is no second caller confirmation bound to those arguments.
- PO creation and appointments are not idempotent across repeated calls; a new row
  is created each time.
- Result dicts are not schema-validated before speech. The grounding guard is a
  separate lexical layer.

These are the gaps the public demo closes, not properties of production.

---

## The public demo version

The demo makes the missing gates concrete:

```python
def execute(session, name, args):
    spec = TOOLS.get(name)
    if spec is None:
        raise Refused("unknown tool")
    if spec.kind == "prohibited":
        raise Refused("prohibited in demo")
    if spec.requires_verified and not session.verified:
        raise Refused("identity required")
    if spec.requires_pin and not session.pin_verified:
        raise Refused("pin required")
    validate_args(spec, args)                 # required/optional/format/unknown keys
    if spec.requires_confirmation and session.confirmed_hash != args_hash(args):
        raise Refused("confirmation required")
    if spec.idempotent and key in session.executed:
        return cached_result
    ...
```

`validate_args` rejects unknown arguments instead of silently ignoring them. That
matters: an ignored argument can make a log or audit entry disagree with the action.

Tests: `test_unknown_argument_is_rejected_before_execution`,
`test_read_requires_verified_identity`, `test_write_requires_pin`,
`test_no_write_executes_without_a_matching_confirmation`.
