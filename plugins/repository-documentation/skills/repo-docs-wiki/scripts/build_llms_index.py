#!/usr/bin/env python3
"""Build a compact docs/llms.txt from repo-docs-wiki page frontmatter.

The output is intended as a low-token entrypoint for LLM agents. It summarizes
what documentation exists, where to start, and which pages are stale or draft.
"""

from __future__ import annotations

import argparse
import datetime as dt
from collections import defaultdict
from pathlib import Path

try:
    from docs_wiki_lint import parse_frontmatter
except Exception:  # pragma: no cover - fallback for direct execution from other cwd
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from docs_wiki_lint import parse_frontmatter

TYPE_ORDER = [
    "index",
    "architecture",
    "decision",
    "module",
    "api",
    "flow",
    "runbook",
    "concept",
    "onboarding",
    "meta",
    "uncategorized",
]


def iter_pages(docs: Path):
    for p in sorted(docs.rglob("*.md")):
        if any(part.startswith(".") for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(text)
        rel = p.relative_to(docs).as_posix()
        title = str(fm.get("title", p.stem.replace("-", " ").title())) if fm else p.stem
        typ = str(fm.get("type", "uncategorized")) if fm else "uncategorized"
        summary = str(fm.get("summary", "No summary.")) if fm else "No summary."
        status = str(fm.get("status", "unknown")) if fm else "unknown"
        yield {
            "path": rel,
            "title": title,
            "type": typ,
            "summary": summary,
            "status": status,
        }


def build(docs: Path) -> str:
    pages = list(iter_pages(docs))
    groups = defaultdict(list)
    for page in pages:
        groups[page["type"]].append(page)

    today = dt.date.today().isoformat()
    lines = [
        "# llms.txt - Repository Documentation Entry Point",
        "",
        f"Generated: {today}",
        "",
        "Purpose: compact routing map for LLM agents reading this repository's docs/ wiki.",
        "Source of truth: repository code, tests, configs, schemas, CI, and source-backed docs pages.",
        "Start with: docs/index.md, then follow the smallest relevant page set.",
        "",
        "Rules for agents:",
        "- Verify implementation-sensitive claims against source before acting.",
        "- Treat draft/stale/deprecated pages as lower confidence.",
        "- File durable answers back into docs/ when maintaining documentation.",
        "",
        "## Pages",
        "",
    ]
    emitted = set()
    for typ in TYPE_ORDER + sorted(k for k in groups if k not in TYPE_ORDER):
        items = groups.get(typ, [])
        if not items:
            continue
        emitted.add(typ)
        lines.append(f"### {typ}")
        for page in items:
            lines.append(
                f"- docs/{page['path']} - {page['title']} - {page['summary']} [status: {page['status']}]"
            )
        lines.append("")

    if not pages:
        lines.append("No Markdown documentation pages found yet.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build docs/llms.txt from docs page frontmatter."
    )
    parser.add_argument("--docs", default="docs", help="Docs directory. Default: docs")
    parser.add_argument(
        "--output", default=None, help="Output path. Default: <docs>/llms.txt"
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write output file instead of printing to stdout",
    )
    args = parser.parse_args()

    docs = Path(args.docs).resolve()
    output = Path(args.output).resolve() if args.output else docs / "llms.txt"
    content = build(docs)
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"updated {output}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
