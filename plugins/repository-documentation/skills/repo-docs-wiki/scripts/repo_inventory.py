#!/usr/bin/env python3
"""Print a lightweight repository inventory for docs-wiki bootstrap planning."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".idea",
    ".vscode",
}
MANIFEST_NAMES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "Makefile",
    "justfile",
    "Taskfile.yml",
}
DOC_NAMES = {"README.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "NOTICE"}
TEST_HINTS = {"test", "tests", "spec", "specs", "__tests__"}


def git_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return Path(out.strip())
    except Exception:
        return Path.cwd()


def git_status(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "status", "--short"], cwd=root, text=True, stderr=subprocess.DEVNULL
        )
        return [line for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        current = Path(dirpath)
        for name in filenames:
            p = current / name
            rel = p.relative_to(root)
            if any(part in EXCLUDE_DIRS for part in rel.parts):
                continue
            yield rel


def inventory(root: Path) -> dict:
    files = list(walk(root))
    ext_counts = Counter(p.suffix.lower() or "[none]" for p in files)
    top_dirs = Counter(p.parts[0] for p in files if len(p.parts) > 1)
    manifests = [str(p) for p in files if p.name in MANIFEST_NAMES]
    docs = [str(p) for p in files if p.parts[0] == "docs" or p.name in DOC_NAMES]
    tests = [
        str(p)
        for p in files
        if any(
            part.lower() in TEST_HINTS or part.lower().startswith("test_")
            for part in p.parts
        )
    ]
    ci = [
        str(p)
        for p in files
        if p.parts[:2] == (".github", "workflows")
        or ".gitlab-ci" in p.name
        or p.parts[0] in {".circleci"}
    ]
    source_candidates = []
    for p in files:
        if p.parts[0] in {
            "src",
            "app",
            "lib",
            "packages",
            "services",
            "cmd",
            "internal",
            "pkg",
        }:
            source_candidates.append(str(p))
    return {
        "root": str(root),
        "git_status": git_status(root),
        "file_count": len(files),
        "top_dirs": dict(top_dirs.most_common(20)),
        "extensions": dict(ext_counts.most_common(20)),
        "manifests": manifests[:100],
        "docs": docs[:200],
        "tests_sample": tests[:100],
        "ci": ci[:100],
        "source_candidates_sample": source_candidates[:200],
    }


def print_markdown(data: dict) -> None:
    print("# Repository Inventory")
    print()
    print(f"Root: `{data['root']}`")
    print(f"Files scanned: {data['file_count']}")
    print()
    print("## Git status")
    if data["git_status"]:
        for line in data["git_status"]:
            print(f"- `{line}`")
    else:
        print("- clean or git unavailable")
    print()
    for key, title in [
        ("manifests", "Manifests"),
        ("docs", "Docs"),
        ("ci", "CI"),
        ("tests_sample", "Tests sample"),
        ("source_candidates_sample", "Source candidates sample"),
    ]:
        print(f"## {title}")
        vals = data[key]
        if vals:
            for item in vals:
                print(f"- `{item}`")
        else:
            print("- none detected")
        print()
    print("## Top directories")
    for k, v in data["top_dirs"].items():
        print(f"- `{k}`: {v}")
    print()
    print("## Extensions")
    for k, v in data["extensions"].items():
        print(f"- `{k}`: {v}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print repository inventory for docs-wiki planning."
    )
    parser.add_argument(
        "--root", default=None, help="Repository root; defaults to git root or cwd."
    )
    parser.add_argument(
        "--markdown", action="store_true", help="Print Markdown instead of JSON."
    )
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else git_root().resolve()
    data = inventory(root)
    if args.markdown:
        print_markdown(data)
    else:
        print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
