#!/usr/bin/env python3
"""Lint a repo-docs-wiki docs/ directory.

Checks:
- required seed files
- YAML-ish frontmatter presence and required fields
- source_refs paths exist when they look like repo paths
- Markdown relative links resolve

This is intentionally lightweight and dependency-free.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

REQUIRED_ROOT_FILES = ["index.md", "_meta/schema.md", "_meta/log.md"]
REQUIRED_FIELDS = [
    "title",
    "type",
    "summary",
    "tags",
    "source_refs",
    "status",
    "updated",
]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SOURCE_REF_RE = re.compile(r"^([^#@]+)(?:#L\d+(?:-L\d+)?|@[0-9a-fA-F]{7,40})?$")


@dataclass
class Finding:
    severity: str
    path: str
    message: str


FrontmatterValue = str | list[str]


def parse_frontmatter(text: str) -> tuple[dict[str, FrontmatterValue], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, FrontmatterValue] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            values = data.get(current_key)
            if not isinstance(values, list):
                values = []
                data[current_key] = values
            values.append(line[4:].strip())
            continue
        if ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            current_key = key
            if val == "[]":
                data[key] = []
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                data[key] = [
                    x.strip().strip("'\"") for x in inner.split(",") if x.strip()
                ]
            elif val == "":
                data[key] = []
            else:
                data[key] = val.strip("'\"")
    return data, body


def iter_md_files(docs: Path) -> Iterable[Path]:
    for p in docs.rglob("*.md"):
        if any(part.startswith(".") for part in p.parts):
            continue
        yield p


def link_target_exists(page: Path, target: str, docs: Path) -> bool:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return True
    target = target.split("#", 1)[0].strip()
    if not target:
        return True
    return (page.parent / target).resolve().exists()


def source_path_exists(ref: str, repo_root: Path) -> bool:
    ref = ref.strip().strip("`")
    if not ref or ref.startswith(("inference:", "http://", "https://")):
        return True
    match = SOURCE_REF_RE.match(ref)
    if not match:
        return True
    path_part = match.group(1)
    # Ignore prose-like refs and docs-only refs without path separators when ambiguous.
    if " " in path_part:
        return True
    return (repo_root / path_part).exists()


def lint(docs: Path, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not docs.exists():
        return [Finding("critical", str(docs), "docs directory does not exist")]

    for required_rel in REQUIRED_ROOT_FILES:
        if not (docs / required_rel).exists():
            findings.append(
                Finding(
                    "critical",
                    str(docs / required_rel),
                    "required docs-wiki file is missing",
                )
            )

    pages = list(iter_md_files(docs))
    linked: set[Path] = set()

    for page in pages:
        page_rel = (
            page.relative_to(repo_root) if page.is_relative_to(repo_root) else page
        )
        text = page.read_text(encoding="utf-8", errors="replace")
        fm, _body = parse_frontmatter(text)
        if not fm:
            findings.append(Finding("high", str(page_rel), "missing YAML frontmatter"))
        else:
            for field in REQUIRED_FIELDS:
                if field not in fm:
                    findings.append(
                        Finding(
                            "medium",
                            str(page_rel),
                            f"missing frontmatter field: {field}",
                        )
                    )
            refs = fm.get("source_refs", [])
            if isinstance(refs, str):
                refs = [refs]
            if not refs and fm.get("type") not in {"index", "meta"}:
                findings.append(
                    Finding(
                        "medium",
                        str(page_rel),
                        "non-meta page has empty source_refs",
                    )
                )
            if isinstance(refs, list):
                for ref in refs:
                    if not source_path_exists(str(ref), repo_root):
                        findings.append(
                            Finding(
                                "high",
                                str(page_rel),
                                f"source_ref path not found: {ref}",
                            )
                        )

        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if target_path:
                resolved = (page.parent / target_path).resolve()
                linked.add(resolved)
            if not link_target_exists(page, target, docs):
                findings.append(
                    Finding("medium", str(page_rel), f"broken Markdown link: {target}")
                )

    index_path = (docs / "index.md").resolve()
    for page in pages:
        if page.resolve() == index_path or "_meta" in page.parts:
            continue
        if page.resolve() not in linked:
            page_rel = (
                page.relative_to(repo_root) if page.is_relative_to(repo_root) else page
            )
            findings.append(
                Finding(
                    "low",
                    str(page_rel),
                    "possible orphan page: no inbound Markdown link detected",
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint repo docs wiki.")
    parser.add_argument("docs", nargs="?", default="docs", help="Docs directory.")
    parser.add_argument(
        "--repo-root", default=".", help="Repository root for source_ref path checks."
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    docs = (
        (repo_root / args.docs).resolve()
        if not Path(args.docs).is_absolute()
        else Path(args.docs).resolve()
    )
    findings = lint(docs, repo_root)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        if not findings:
            print("docs-wiki lint: no findings")
        else:
            print(f"docs-wiki lint: {len(findings)} finding(s)")
            for f in findings:
                print(f"[{f.severity}] {f.path}: {f.message}")
    return 1 if any(f.severity in {"critical", "high"} for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
