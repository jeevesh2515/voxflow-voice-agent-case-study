#!/usr/bin/env python3
"""Check relative Markdown links and heading anchors in the public staging tree.

Usage:
    python3 scripts/check_links.py
    python3 scripts/check_links.py --self-test

External URLs are not fetched: the repository must stay offline and deterministic.
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
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def slugify(text: str) -> str:
    text = re.sub(r"`", "", text)
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text


def anchors_for(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    in_fence = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = slugify(match.group(2))
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def iter_markdown(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def check(root: Path) -> list[str]:
    problems: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}

    def anchors(path: Path) -> set[str]:
        if path not in anchor_cache:
            anchor_cache[path] = anchors_for(path)
        return anchor_cache[path]

    for path in iter_markdown(root):
        rel = path.relative_to(root)
        in_fence = False
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for raw_target in LINK_RE.findall(line):
                target = raw_target.strip()
                if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                    continue
                if target.startswith("#"):
                    if target[1:] and target[1:] not in anchors(path):
                        problems.append(f"{rel}:{number}: missing anchor {target}")
                    continue
                file_part, _, fragment = target.partition("#")
                if not file_part:
                    continue
                destination = (path.parent / file_part).resolve()
                if not destination.exists():
                    problems.append(f"{rel}:{number}: missing link target {target}")
                    continue
                if fragment and destination.suffix == ".md":
                    if fragment not in anchors(destination):
                        problems.append(f"{rel}:{number}: missing anchor {target}")
    return problems


def self_test() -> int:
    temp = Path(tempfile.mkdtemp(prefix="voxflow-links-"))
    try:
        (temp / "b.md").write_text("# Target heading\n", encoding="utf-8")
        (temp / "a.md").write_text(
            "[good](b.md)\n"
            "[anchor](b.md#target-heading)\n"
            "[bad](missing.md)\n"
            "[bad anchor](b.md#nope)\n"
            "```\n[ignored](missing.md)\n```\n",
            encoding="utf-8",
        )
        problems = check(temp)
        expected = 2
        if len(problems) != expected:
            print(f"SELF-TEST FAIL: expected {expected} problems, got {problems}")
            return 1
        print(f"self-test: {expected} expected problems detected")
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
        print(f"LINK CHECK FAILED: {len(problems)} problem(s)\n")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("LINK CHECK PASSED: all relative links and anchors resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
