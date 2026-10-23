# Excerpt 01 — PIN storage and supplier binding

**Source:** private VoxFlow repository, commit `5acef5f`, files
`services/pin_security.py` and `agent/tools.py`. Abridged; comments removed.
**Why it is safe:** contains no secret, customer data, prompt or schema. The
algorithm and binding pattern are the point.

---

## What to notice

1. PINs are never stored or compared in plaintext.
2. A malformed stored hash fails closed.
3. Verification is constant-time.
4. The PIN is bound to a **supplier**, not just to a boolean on the session.
5. The PIN is redacted from persisted speech/tool text.

---

## Storage and verification

```python
PIN_SCHEME = "pbkdf2_sha256"
PIN_ITERATIONS = 310_000
PIN_SALT_BYTES = 16
PIN_DIGEST_BYTES = 32


def validate_pin(pin: str) -> str:
    normalized = (pin or "").strip()
    if not normalized.isascii() or not normalized.isdigit() or not 4 <= len(normalized) <= 8:
        raise ValueError("pin_must_be_4_to_8_digits")
    return normalized


def hash_pin(pin: str) -> str:
    normalized = validate_pin(pin)
    salt = secrets.token_bytes(PIN_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        salt,
        PIN_ITERATIONS,
        dklen=PIN_DIGEST_BYTES,
    )
    return "$".join(
        (
            PIN_SCHEME,
            str(PIN_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_pin_hash(pin: str, encoded_hash: str | None) -> bool:
    if not encoded_hash:
        return False
    try:
        normalized = validate_pin(pin)
        scheme, iterations_raw, salt_raw, expected_raw = encoded_hash.split("$", 3)
        if scheme != PIN_SCHEME:
            return False
        iterations = int(iterations_raw)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_raw.encode("ascii"))
        if len(salt) < 16 or len(expected) != PIN_DIGEST_BYTES:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", normalized.encode("utf-8"), salt, iterations, dklen=len(expected)
        )
    except (TypeError, ValueError, UnicodeError):
        return False
    return hmac.compare_digest(actual, expected)
```

**Design notes**

- A per-PIN random salt prevents rainbow tables and cross-account comparison.
- The iteration count is stored in the hash, so it can be raised later without a
  flag day; the verifier rejects absurd values.
- Any parse error returns `False`; there is no “treat as valid” branch.
- `hmac.compare_digest` avoids a timing oracle.

**Limits**

- 4–8 digits is a weak secret space. PBKDF2 slows guessing; it does not make a
  shared depot PIN strong.
- There is no breached-PIN check or per-caller-number throttle at this layer.
- The private product has a legacy plaintext migration path; this excerpt shows only
  the target scheme.

---

## Binding the PIN to a supplier

A session boolean is not enough. If the caller re-identifies as another supplier,
the old PIN must not authorise the new account.

```python
_PIN_BINDING_KEY = "_pin_verified_supplier_id"


def _bound_supplier_id(session: CallSession, key: str) -> str | None:
    supplier_id = session.route_policy.get(key)
    return supplier_id if isinstance(supplier_id, str) and supplier_id else None


def _pin_authorized_supplier_id(session: CallSession) -> str | None:
    supplier_id = session.supplier_id
    if (
        supplier_id
        and session.pin_verified
        and _bound_supplier_id(session, _PIN_BINDING_KEY) == supplier_id
    ):
        return supplier_id
    return None
```

Used by the high-impact write:

```python
async def create_po(session, supplier_id=None, items=None, notes=""):
    authorized_supplier_id = _pin_authorized_supplier_id(session)
    if authorized_supplier_id is None:
        log.warning("security.tier2_blocked", ...)
        return {
            "ok": False,
            "error": "pin_required",
            "message": "Tier 2 PIN verification is required before placing a purchase order.",
        }
    ...
```

When the identified supplier changes, the product clears both the knowledge and PIN
bindings:

```python
def _clear_authorization(session: CallSession) -> None:
    session.verified = False
    session.pin_verified = False
    policy = session.route_policy
    policy.pop(_KNOWLEDGE_BINDING_KEY, None)
    policy.pop(_PIN_BINDING_KEY, None)
```

**Why this matters:** PIN verification for supplier A cannot be replayed against
supplier B. The check is a three-part conjunction: current supplier exists, PIN flag
is true, and the persisted binding equals the current supplier.

**What this does not do:** it does not ask the caller to confirm the order, slot,
quantity or status. A valid PIN plus a misheard reference can still create the wrong
PO. That is why [TOOL-SAFETY.md](../TOOL-SAFETY.md) calls the confirmation gate the
top unresolved risk.

---

## Redaction

```python
_SPOKEN_PIN_RE = re.compile(r"(?<!\d)\d{4,8}(?!\d)")


def redact_pin_text(text: str) -> str:
    return _SPOKEN_PIN_RE.sub("[REDACTED PIN]", text or "")
```

The lookarounds avoid mangling longer numeric IDs. This runs before tool JSON is
persisted. It is a backstop, not permission to log raw speech.

---

## What the public demo does differently

The demo stores synthetic PINs in plain fixture data because it demonstrates policy,
not storage. It does implement the same binding idea: a PIN verified for
`acct_synthetic_001` cannot authorise a write for `acct_synthetic_002`.

Relevant tests: `test_write_requires_pin`, `test_audit_events_never_contain_the_pin`,
`test_changing_order_invalidates_pending_confirmation`.
