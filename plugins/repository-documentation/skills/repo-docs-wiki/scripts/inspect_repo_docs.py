#!/usr/bin/env python3
"""Inspect a repository and its docs wiki state.

Outputs enough context for an agent to decide whether to init, ingest, query, or lint.
This script is read-only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "target",
    ".next",
    ".turbo",
    ".cache",
    "coverage",
    "htmlcov",
    "vendor",
}

LANG_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript/React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".hpp": "C++",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
}

BUILD_FILES = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "uv.lock",
    "poetry.lock",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "Makefile",
    "justfile",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
]


def run(cmd: list[str], cwd: Path | None = None) -> str | None:
    try:
        return subprocess.check_output(
            cmd, cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def repo_root() -> Path:
    root = run(["git", "rev-parse", "--show-toplevel"])
    return Path(root).resolve() if root else Path.cwd().resolve()


def git_available(root: Path) -> bool:
    return (root / ".git").exists() or bool(
        run(["git", "rev-parse", "--git-dir"], cwd=root)
    )


def current_commit(root: Path) -> str | None:
    return run(["git", "rev-parse", "HEAD"], cwd=root)


def git_status(root: Path) -> list[str]:
    status = run(["git", "status", "--porcelain"], cwd=root)
    return status.splitlines() if status else []


def read_state(docs_dir: Path) -> dict[str, Any] | None:
    state_path = docs_dir / "_meta" / "WIKI_STATE.json"
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "path": str(state_path)}


def diff_from_checkpoint(root: Path, checkpoint: str | None) -> list[dict[str, str]]:
    if not checkpoint:
        return []
    text = run(["git", "diff", "--name-status", f"{checkpoint}..HEAD"], cwd=root)
    if not text:
        return []
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            rows.append({"status": status, "old_path": parts[1], "path": parts[2]})
        elif len(parts) >= 2:
            rows.append({"status": status, "path": parts[1]})
    return rows


def staged_and_unstaged_diff(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, cmd in [
        ("unstaged", ["git", "diff", "--name-status"]),
        ("staged", ["git", "diff", "--cached", "--name-status"]),
    ]:
        text = run(cmd, cwd=root)
        if not text:
            continue
        for line in text.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                rows.append({"status": parts[0], "path": parts[-1], "kind": label})
    return rows


def top_level_entries(root: Path) -> list[str]:
    entries = []
    for p in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        if p.name in EXCLUDE_DIRS:
            continue
        entries.append(p.name + ("/" if p.is_dir() else ""))
    return entries[:80]


def count_docs_pages(docs_dir: Path) -> dict[str, Any]:
    if not docs_dir.exists():
        return {"exists": False, "markdown_pages": 0, "pages": []}
    pages = []
    for p in docs_dir.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        pages.append(str(p.relative_to(docs_dir)))
    pages.sort()
    return {"exists": True, "markdown_pages": len(pages), "pages": pages[:200]}


def detect_languages(root: Path) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            lang = LANG_EXTENSIONS.get(ext)
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
    return [
        {"language": k, "files": v}
        for k, v in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def detect_build_files(root: Path) -> list[str]:
    return [name for name in BUILD_FILES if (root / name).exists()]


def detect_candidate_source_dirs(root: Path, docs_dir: Path) -> list[str]:
    candidates = []
    for p in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir() or p.name in EXCLUDE_DIRS:
            continue
        if p.resolve() == docs_dir.resolve():
            continue
        if p.name.startswith(".") and p.name != ".github":
            continue
        # Keep likely source/config dirs, not every random folder.
        if p.name in {
            "src",
            "app",
            "apps",
            "packages",
            "lib",
            "services",
            "server",
            "client",
            "api",
            "cmd",
            "internal",
            "pkg",
            "tests",
            "test",
            "spec",
            "migrations",
            "schemas",
            "deploy",
            "deployment",
            "infra",
            "terraform",
            "k8s",
            ".github",
        }:
            candidates.append(p.name)
    return candidates


def make_report(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    docs_dir = (root / args.docs_dir).resolve()
    state = read_state(docs_dir)
    checkpoint = None
    if isinstance(state, dict):
        checkpoint = state.get("last_ingested_commit")

    report = {
        "repo_root": str(root),
        "docs_dir": str(docs_dir.relative_to(root))
        if docs_dir.is_relative_to(root)
        else str(docs_dir),
        "git_available": git_available(root),
        "current_commit": current_commit(root),
        "working_tree_status": git_status(root),
        "wiki_state": state,
        "checkpoint_diff": diff_from_checkpoint(root, checkpoint),
        "working_tree_diff": staged_and_unstaged_diff(root),
        "docs": count_docs_pages(docs_dir),
        "top_level_entries": top_level_entries(root),
        "candidate_source_dirs": detect_candidate_source_dirs(root, docs_dir),
        "build_files": detect_build_files(root),
        "languages": detect_languages(root),
    }
    return report


def as_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Repo Docs Wiki Inspection")
    lines.append("")
    lines.append(f"- Repo root: `{report['repo_root']}`")
    lines.append(f"- Docs dir: `{report['docs_dir']}`")
    lines.append(f"- Git available: `{str(report['git_available']).lower()}`")
    lines.append(f"- Current commit: `{report.get('current_commit') or 'unknown'}`")
    status = report.get("working_tree_status") or []
    lines.append(f"- Dirty working tree: `{str(bool(status)).lower()}`")
    if status:
        lines.append("- Working tree status:")
        for item in status[:50]:
            lines.append(f"  - `{item}`")
    lines.append("")

    state = report.get("wiki_state")
    lines.append("## Wiki state")
    if state:
        lines.append(f"- Last ingested commit: `{state.get('last_ingested_commit')}`")
        lines.append(f"- Last ingested at: `{state.get('last_ingested_at')}`")
        if state.get("error"):
            lines.append(f"- State error: `{state.get('error')}`")
    else:
        lines.append("- No `docs/_meta/WIKI_STATE.json` found.")
    lines.append("")

    docs = report.get("docs", {})
    lines.append("## Docs")
    lines.append(f"- Exists: `{str(docs.get('exists')).lower()}`")
    lines.append(f"- Markdown pages: `{docs.get('markdown_pages', 0)}`")
    for page in docs.get("pages", [])[:60]:
        lines.append(f"  - `{page}`")
    lines.append("")

    diff = report.get("checkpoint_diff") or []
    lines.append("## Changes since last checkpoint")
    if diff:
        for row in diff[:100]:
            if "old_path" in row:
                lines.append(
                    f"- `{row['status']}` `{row['old_path']}` -> `{row['path']}`"
                )
            else:
                lines.append(f"- `{row['status']}` `{row['path']}`")
    else:
        lines.append(
            "- No committed diff detected from checkpoint, or no checkpoint exists."
        )
    lines.append("")

    wdiff = report.get("working_tree_diff") or []
    lines.append("## Uncommitted changed files")
    if wdiff:
        for row in wdiff[:100]:
            lines.append(f"- `{row.get('kind')}` `{row['status']}` `{row['path']}`")
    else:
        lines.append("- None detected.")
    lines.append("")

    lines.append("## Candidate source dirs")
    for item in report.get("candidate_source_dirs", []):
        lines.append(f"- `{item}`")
    if not report.get("candidate_source_dirs"):
        lines.append("- None detected from common names.")
    lines.append("")

    lines.append("## Build/config files")
    for item in report.get("build_files", []):
        lines.append(f"- `{item}`")
    if not report.get("build_files"):
        lines.append("- None detected from common names.")
    lines.append("")

    lines.append("## Languages")
    for item in report.get("languages", [])[:20]:
        lines.append(f"- {item['language']}: {item['files']} files")
    if not report.get("languages"):
        lines.append("- No common source extensions detected.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect repo docs wiki state.")
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Docs directory relative to repo root. Default: docs",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    report = make_report(args)
    if args.format == "markdown":
        print(as_markdown(report))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
