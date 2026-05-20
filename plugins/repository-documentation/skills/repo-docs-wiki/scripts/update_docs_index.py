#!/usr/bin/env python3
"""Rebuild docs/index.md from docs page frontmatter.

This intentionally preserves a compact generated index. For custom narrative indexes,
use this as a report and apply edits manually.
"""

from __future__ import annotations

import argparse
import datetime as dt
from collections import defaultdict
from pathlib import Path

from docs_wiki_lint import parse_frontmatter

TYPE_ORDER = [
    "architecture",
    "decision",
    "module",
    "api",
    "flow",
    "runbook",
    "concept",
    "onboarding",
    "meta",
    "index",
]


def iter_pages(docs: Path):
    for p in docs.rglob("*.md"):
        if p.name == "index.md":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(text)
        yield p, fm


def rel_link(from_file: Path, to_file: Path) -> str:
    return to_file.relative_to(from_file.parent).as_posix()


def build_index(docs: Path) -> str:
    today = dt.date.today().isoformat()
    groups = defaultdict(list)
    for p, fm in iter_pages(docs):
        typ = str(fm.get("type", "uncategorized")) if fm else "uncategorized"
        title = str(fm.get("title", p.stem.replace("-", " ").title())) if fm else p.stem
        summary = str(fm.get("summary", "No summary.")) if fm else "No summary."
        status = str(fm.get("status", "unknown")) if fm else "unknown"
        groups[typ].append((title, p, summary, status))

    lines = [
        "---",
        "title: Documentation Index",
        "type: index",
        "summary: Catalog of the repository documentation wiki.",
        "tags: [docs-wiki, index]",
        "source_refs: []",
        "status: verified",
        f"updated: {today}",
        "---",
        "",
        "# Documentation Index",
        "",
        "This index is generated from page frontmatter. Use it as the routing table for humans and LLM agents.",
        "",
    ]
    for typ in TYPE_ORDER + sorted(k for k in groups if k not in TYPE_ORDER):
        items = groups.get(typ, [])
        if not items:
            continue
        lines.append(f"## {typ.title()}")
        lines.append("")
        for title, p, summary, status in sorted(items, key=lambda x: str(x[1])):
            link = p.relative_to(docs).as_posix()
            lines.append(f"- [{title}]({link}) - {summary} _status: {status}_")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild docs/index.md from frontmatter."
    )
    parser.add_argument("docs", nargs="?", default="docs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    docs = Path(args.docs).resolve()
    content = build_index(docs)
    if args.dry_run:
        print(content)
    else:
        (docs / "index.md").write_text(content, encoding="utf-8")
        print(f"updated {docs / 'index.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
