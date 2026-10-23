#!/usr/bin/env python3
"""Basic Markdown hygiene check (no external linter required).

Checks:
  - balanced fenced code blocks;
  - exactly one top-level heading per file;
  - final newline;
  - no tab characters outside fences;
  - no trailing whitespace;
  - no TODO/TBD/FIXME/lorem ipsum placeholders.

Usage:
    python3 scripts/check_markdown.py
    python3 scripts/check_markdown.py --self-test
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
FENCE_RE = re.compile(r"^\s*(```|~~~)")
H1_RE = re.compile(r"^#\s+\S")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|lorem ipsum)\b", re.I)


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not text.endswith("\n"):
        problems.append("missing final newline")

    fences = 0
    h1_count = 0
    for number, line in enumerate(lines, start=1):
        if FENCE_RE.match(line):
            fences += 1
            continue
        if fences % 2 == 1:
            continue
        if H1_RE.match(line):
            h1_count += 1
        if "\t" in line:
            problems.append(f"line {number}: tab outside code fence")
        if line != line.rstrip():
            problems.append(f"line {number}: trailing whitespace")
        if PLACEHOLDER_RE.search(line):
            problems.append(f"line {number}: placeholder text")

    if fences % 2 != 0:
        problems.append("unbalanced code fence")
    if h1_count != 1:
        problems.append(f"expected exactly one H1, found {h1_count}")
    return problems


def check(root: Path) -> list[str]:
    problems: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for problem in check_file(path):
            problems.append(f"{path.relative_to(root)}: {problem}")
    return problems


def self_test() -> int:
    temp = Path(tempfile.mkdtemp(prefix="voxflow-md-"))
    try:
        (temp / "good.md").write_text("# Title\n\nText.\n", encoding="utf-8")
        (temp / "bad.md").write_text(
            "# One\n# Two\n\nTODO\n\tindent\ntrailing   ",
            encoding="utf-8",
        )
        (temp / "unbalanced.md").write_text(
            "# Title\n\n```\nunclosed\n",
            encoding="utf-8",
        )
        found = check(temp)
        expected_fragments = ["found 2", "placeholder", "tab", "trailing", "final newline", "unbalanced"]
        missing = [fragment for fragment in expected_fragments if not any(fragment in item for item in found)]
        if missing:
            print(f"SELF-TEST FAIL: missing {missing}; got {found}")
            return 1
        print(f"self-test: {len(found)} expected problems detected")
        return 0
    finally:
        shutil.rmtree(temp)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    problems = check(ROOT)
    if problems:
        print(f"MARKDOWN CHECK FAILED: {len(problems)} problem(s)\n")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("MARKDOWN CHECK PASSED: fences, headings and whitespace are clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
