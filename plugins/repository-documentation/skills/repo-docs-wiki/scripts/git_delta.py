#!/usr/bin/env python3
"""Report git changes relevant to docs-wiki ingest.

Reads docs/_meta/state.json if present and compares last_ingested_commit to HEAD.
Falls back to working-tree status when no marker exists.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def run_git(args: list[str], root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def load_state(docs: Path) -> dict[str, str]:
    p = docs / "_meta" / "state.json"
    if not p.exists():
        return {}
    try:
        data: Any = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): value for key, value in data.items() if isinstance(value, str)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report git delta for docs-wiki ingest."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--base", default=None, help="Base commit override.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    docs = root / args.docs_dir
    head = run_git(["rev-parse", "HEAD"], root)
    state = load_state(docs)
    base = (
        args.base
        or state.get("last_ingested_commit")
        or state.get("last_bootstrap_commit")
    )

    if base and head:
        out = run_git(["diff", "--name-status", f"{base}..{head}"], root) or ""
        changes = [line for line in out.splitlines() if line.strip()]
    else:
        out = run_git(["status", "--short"], root) or ""
        changes = [line for line in out.splitlines() if line.strip()]

    result = {"repo_root": str(root), "base": base, "head": head, "changes": changes}

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"repo: {result['repo_root']}")
        print(f"base: {base or '[none]'}")
        print(f"head: {head or '[none]'}")
        print("changes:")
        if changes:
            for line in changes:
                print(f"  {line}")
        else:
            print("  [none]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
