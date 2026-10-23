# Excerpt 04 — Signed Connect bridge

**Source:** private VoxFlow repository, commit `5acef5f`,
`deploy/aws/lambda_handler.py` and `telephony/connect_provider.py`. Abridged.
**Why it is safe:** placeholder URL, no secret value, no account or phone identifier.

---

## Why the bridge is a trust boundary

Amazon Connect invokes a Lambda for each turn. The Lambda calls the API over HTTP.
Without verification, anyone who can reach the API could forge a turn, choose a
tenant DID, and read or write data without a phone call.

The bridge therefore signs:

```text
timestamp ":" path ":" exact_request_body
```

with a shared secret, and sends the signature and timestamp as headers.

---

## Signing (Lambda side)

```python
def _sign_request(secret: str, timestamp: str, path: str, body: bytes) -> str:
    message = (
        timestamp.encode("utf-8")
        + b":"
        + path.encode("utf-8")
        + b":"
        + body
    )
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _post_json(url: str, payload: dict, secret: str, path: str) -> dict:
    if not secret:
        raise RuntimeError("VOXFLOW_SECRET is required")   # fail closed

    data = json.dumps(payload).encode("utf-8")
    timestamp = str(time.time())
    signature = _sign_request(secret, timestamp, path, data)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "VoxFlow-AWS-Connect-Bridge/1.0",
        "x-voxflow-signature": signature,
        "x-voxflow-timestamp": timestamp,
    }
    ...
```

The body is serialised once and the **same bytes** are signed and sent. Re-encoding
after signing is a classic source of signature mismatches.

---

## Verification (API side)

```python
def validate_webhook(self, request, form, path) -> bool:
    settings = get_settings()
    secret = (
        getattr(settings, "connect_lambda_secret", "")
        or settings.provider_callback_shared_secret
    )
    production = _is_production(settings)
    if production and not secret:
        log.error("connect.signing_secret_missing")
        return False
    if not secret:
        return True
    if not production and not settings.provider_callback_validate_signature:
        return True

    signature = request.headers.get("x-voxflow-signature", "")
    timestamp = request.headers.get("x-voxflow-timestamp", "")
    raw_body = getattr(request.state, "connect_raw_body", None)
    if not signature or not timestamp or not isinstance(raw_body, bytes):
        return False

    try:
        sent_at = float(timestamp)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(sent_at):
        return False

    max_age = max(
        1,
        min(int(settings.provider_callback_max_age_seconds), _MAX_SIGNATURE_AGE_SECONDS),
    )
    now = time.time()
    if abs(now - sent_at) > max_age:
        log.warning("connect.stale_request", age=round(abs(now - sent_at), 3))
        return False

    message = (
        timestamp.encode("utf-8")
        + b":"
        + path.encode("utf-8")
        + b":"
        + raw_body
    )
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False
    if not _consume_signature_hash(signature, now, max_age):
        log.warning("connect.replay_detected")
        request.state.connect_replay_detected = True
        return False
    return True
```

**Properties**

- Production with no secret → reject. There is no “development default” in prod.
- Stale timestamp → reject (window capped at 300 s).
- Signature mismatch → reject in constant time.
- Signature reuse within the window → reject via the replay ledger.
- Non-production may bypass signature checks only when explicitly configured to do
  so; that path is not a production fallback.

**Limits**

- One shared secret, no per-tenant keys or documented rotation.
- Clock skew can reject valid turns; operators need a runbook.
- The in-memory replay ledger is per-process. With multiple instances, Redis is
  required; if configured Redis is unreachable in production, the check fails
  closed rather than reopening the window.

---

## Replay ledger

```python
def _consume_signature_hash(signature: str, now: float, window: int) -> bool:
    redis_url = getattr(settings, "redis_url", "") or os.getenv("REDIS_URL", "")
    signature_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()

    if redis_url:
        try:
            r = _get_redis_client(redis_url)
            key = f"voxflow:replay:{signature_hash}"
            acquired = r.set(key, str(now), nx=True, ex=window)
            return bool(acquired)
        except Exception as exc:
            if _is_production(settings):
                log.error("connect.replay_redis_unreachable_fail_closed error=%s", exc)
                return False
            log.warning("connect.replay_redis_fallback error=%s", exc)

    # process-local fallback for single-instance / development
    ...
```

This is the right shape: a shared atomic operation for the multi-instance case, and
an explicit fail-closed decision when the shared ledger is down in production.

---

## What to test

The private suite has dedicated bridge tests. The behaviours worth preserving:

1. A real Lex transcript reaches `/api/connect/turn` unchanged.
2. A missing secret raises before any HTTP call.
3. A bad signature is rejected.
4. A stale timestamp is rejected.
5. A replayed signature is rejected.
6. The API receives the exact signed bytes.
7. A failed API call does not produce a fake agent reply.

The public repository does not reproduce the bridge; it has no network or secret.
The excerpt exists to show the boundary and the fail-closed decisions.
