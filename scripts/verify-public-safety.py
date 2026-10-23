#!/usr/bin/env python3
"""Fail closed if the public staging tree contains secrets, private data or
unsupported product claims.

Usage:
    python3 scripts/verify-public-safety.py
    python3 scripts/verify-public-safety.py --self-test

This is a heuristic gate, not a replacement for human review. It deliberately
skips its own source because the patterns are the content.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
SKIP_FILES = {Path(__file__).resolve()}
MAX_BYTES = 2_000_000

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("provider API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("Stripe live key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}\b")),
    ("Stripe webhook secret", re.compile(r"\bwhsec_[A-Za-z0-9]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("database URL with credentials", re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:/]+:[^\s@]+@")),
    ("secret assignment", re.compile(
        r"(?i)\b(?:SUPABASE_SERVICE_ROLE_KEY|STRIPE_SECRET_KEY|GROQ_API_KEY|"
        r"OPENAI_API_KEY|ANTHROPIC_API_KEY|CONNECT_LAMBDA_SECRET|"
        r"AWS_SECRET_ACCESS_KEY)\s*=\s*\S+"
    )),
]

PRIVATE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("UK mobile number", re.compile(r"(?:\+44\s?7|07)\d{3}[\s-]?\d{6}\b")),
    ("international phone number", re.compile(r"\+\d{1,3}\s?\(?\d{1,4}\)?[\s.-]\d{3,4}[\s.-]\d{3,4}\b")),
    ("private domain", re.compile(r"(?i)\b(?:voxflow\.(?:cc|ai|co\.uk)|supabase\.co|onrender\.com|render\.com|vercel\.app)\b")),
    ("AWS hostname", re.compile(r"(?i)\b(?:amazonaws\.com|execute-api\.[a-z0-9-]+|rds\.amazonaws\.com)\b")),
    ("private repo owner", re.compile(r"(?i)jeevesh2515|jeeveshsingale|github\.com/jeevesh")),
    ("absolute home path", re.compile(r"(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\\\Users\\\\)")),
    ("internal worktree path", re.compile(r"(?:\.delta/|voxflow-voice-agent/)")),
]

CLAIM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("production-ready", re.compile(r"\bproduction[- ]ready\b", re.I)),
    ("SOC 2", re.compile(r"\bSOC ?2\b", re.I)),
    ("ISO 27001", re.compile(r"\bISO ?27001\b", re.I)),
    ("GDPR compliant", re.compile(r"\bGDPR[- ]compliant\b", re.I)),
    ("PCI DSS", re.compile(r"\bPCI[- ]DSS\b", re.I)),
    ("zero hallucination", re.compile(r"\bzero[- ]hallucination\b", re.I)),
    ("100% accurate", re.compile(r"\b100\s?%\s?(?:accurate|accuracy)\b", re.I)),
    ("sub-400 ms", re.compile(r"\bsub[- ]?400\s?ms\b", re.I)),
    ("822 ms", re.compile(r"\b822\s?ms\b", re.I)),
    ("12,000 minutes", re.compile(r"\b12,000\b")),
    ("real customers", re.compile(r"\b(?:real|live|paying)\s+customers?\b", re.I)),
    ("revenue", re.compile(r"\brevenue\b", re.I)),
    ("barge-in", re.compile(r"\bbarge[- ]in\b", re.I)),
    ("zero PII", re.compile(r"\bzero\s+PII\b", re.I)),
    ("complete erasure", re.compile(r"\bcomplete\s+erasure\b", re.I)),
    ("enterprise-grade", re.compile(r"\benterprise[- ]grade\b", re.I)),
    ("fully autonomous", re.compile(r"\b(?:fully|100%)\s+autonomous\b", re.I)),
    ("guaranteed", re.compile(r"\bguarantee(?:d|s)?\b", re.I)),
]

NEGATIVE_RE = re.compile(
    r"(?i)\b(?:not|no|never|cannot|can't|don't|do not|doesn't|does not|"
    r"must not|mustn't|avoid|forbidden|prohibited|without|unsupported|"
    r"mislabelled|mislabeled|not measured|not certified|not compliant|"
    r"instead of|rather than|neither|isn't|aren't|won't|wouldn't|shouldn't|"
    r"no evidence|zero evidence)\b"
)

IGNORE_START = "<!-- safety-scan:ignore-claims-start -->"
IGNORE_END = "<!-- safety-scan:ignore-claims-end -->"


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.resolve() in SKIP_FILES:
            continue
        yield path


def _read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan(root: Path) -> list[str]:
    findings: list[str] = []

    for path in _iter_files(root):
        rel = path.relative_to(root)
        if path.is_symlink():
            findings.append(f"{rel}: symlink not allowed in public staging")
            continue
        if path.stat().st_size > MAX_BYTES:
            findings.append(f"{rel}: file exceeds {MAX_BYTES} bytes")
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            findings.append(f"{rel}: environment file not allowed")
            continue

        text = _read_text(path)
        if text is None:
            findings.append(f"{rel}: binary file not allowed")
            continue

        lines = text.splitlines()
        in_ignored_claims = False
        is_svg = path.suffix.lower() == ".svg"
        for number, line in enumerate(lines, start=1):
            if IGNORE_START in line:
                in_ignored_claims = True
                continue
            if IGNORE_END in line:
                in_ignored_claims = False
                continue

            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{number}: possible {label}")

            # Base64 font blobs in rendered SVGs look like digit runs. Scan the
            # visible text for private identifiers, not the embedded font data.
            for label, pattern in PRIVATE_PATTERNS:
                if is_svg and label in {"email address", "UK mobile number", "international phone number"}:
                    continue
                if pattern.search(line):
                    findings.append(f"{rel}:{number}: {label}")

            if in_ignored_claims:
                continue

            # Claims are often wrapped across lines. Allow a nearby negation to
            # cover the sentence ("It is not yet\nproduction-ready").
            context_start = max(0, number - 3)
            context_end = min(len(lines), number + 2)
            context = " ".join(lines[context_start:context_end])
            if NEGATIVE_RE.search(context):
                continue
            for label, pattern in CLAIM_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{number}: unsupported claim: {label}")

    return findings


def self_test() -> int:
    cases = [
        ("clean-negative.md", "This is not production-ready.\n", 0),
        ("clean-neutral.md", "The demo is synthetic.\n", 0),
        ("bad-secret.txt", "AKIA" + "A" * 16 + "\n", 1),
        ("bad-email.md", "Contact someone@example.com\n", 1),
        ("bad-phone.md", "Call +44 7700 900123\n", 1),
        ("bad-claim.md", "We are production-ready.\n", 1),
        ("bad-host.md", "Deployed at https://example.render.com\n", 1),
        ("ignored-claim.md", f"{IGNORE_START}\nproduction-ready\n{IGNORE_END}\n", 0),
        ("bad-path.md", "See /Users/someone/project\n", 1),
    ]
    failures = 0
    for name, content, expected in cases:
        temp = Path(tempfile.mkdtemp(prefix="voxflow-safety-"))
        try:
            (temp / name).write_text(content, encoding="utf-8")
            found = scan(temp)
            if (1 if found else 0) != expected:
                failures += 1
                print(f"SELF-TEST FAIL: {name}: expected {expected}, got {found}")
        finally:
            shutil.rmtree(temp)
    if failures:
        print(f"self-test: {failures} failure(s)")
        return 1
    print(f"self-test: {len(cases)} cases passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    findings = scan(ROOT)
    if findings:
        print(f"PUBLIC-SAFETY SCAN FAILED: {len(findings)} finding(s)\n")
        for finding in findings:
            print(f"  {finding}")
        print("\nFix the finding or, for an intentional negative example, rewrite it "
              "so the line contains an explicit negation.")
        return 1
    print("PUBLIC-SAFETY SCAN PASSED: no secrets, private identifiers or unsupported claims found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
