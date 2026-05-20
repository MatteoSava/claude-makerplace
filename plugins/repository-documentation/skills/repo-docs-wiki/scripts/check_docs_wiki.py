#!/usr/bin/env python3
"""Check docs wiki health.

This script performs deterministic checks that are useful before an LLM lint pass:
- broken relative Markdown links
- pages missing from INDEX.md
- INDEX.md entries pointing to missing pages
- frontmatter source_refs paths that no longer exist
- stale checkpoint hints when Git diff exists

It does not try to judge semantic contradictions; the LLM should do that part.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_PATH_RE = re.compile(r"^\s*path:\s*[\"']?([^\"'\n]+)[\"']?\s*$")
INDEX_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)")

EXCLUDE_PARTS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
}


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


def normalize_link(raw: str) -> str | None:
    link = raw.strip()
    if not link or link.startswith("#"):
        return None
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link):
        return None
    link = link.split("#", 1)[0]
    link = link.split("?", 1)[0]
    if not link:
        return None
    return link


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.parts)


def md_pages(docs_dir: Path) -> list[Path]:
    if not docs_dir.exists():
        return []
    return sorted([p for p in docs_dir.rglob("*.md") if not is_excluded(p)])


def path_exists_for_link(source_file: Path, link: str) -> bool:
    target = (source_file.parent / link).resolve()
    if target.exists():
        return True
    if target.suffix == "" and target.with_suffix(".md").exists():
        return True
    return False


def check_links(docs_dir: Path) -> list[dict[str, str]]:
    broken: list[dict[str, str]] = []
    for page in md_pages(docs_dir):
        text = page.read_text(encoding="utf-8", errors="ignore")
        for match in LINK_RE.finditer(text):
            link = normalize_link(match.group(1))
            if not link:
                continue
            if not path_exists_for_link(page, link):
                broken.append(
                    {
                        "page": str(page.relative_to(docs_dir)),
                        "link": match.group(1).strip(),
                    }
                )
    return broken


def find_index_path(docs_dir: Path) -> Path:
    for name in ("index.md", "INDEX.md"):
        candidate = docs_dir / name
        if candidate.exists():
            return candidate
    return docs_dir / "index.md"


def check_index(docs_dir: Path) -> dict[str, Any]:
    index = find_index_path(docs_dir)
    pages = [p for p in md_pages(docs_dir) if p.resolve() != index.resolve()]
    if not index.exists():
        return {
            "index_exists": False,
            "index_path": str(index),
            "pages_missing_from_index": [str(p.relative_to(docs_dir)) for p in pages],
            "index_links_to_missing_pages": [],
        }
    text = index.read_text(encoding="utf-8", errors="ignore")
    missing = []
    for page in pages:
        rel = str(page.relative_to(docs_dir)).replace("\\", "/")
        if rel not in text and f"./{rel}" not in text:
            # Do not require internal source notes to appear if they are intentionally private.
            if not rel.startswith("_sources/"):
                missing.append(rel)

    missing_targets = []
    for match in INDEX_LINK_RE.finditer(text):
        link = normalize_link(match.group(1))
        if not link:
            continue
        target = (index.parent / link).resolve()
        if not target.exists():
            missing_targets.append(link)
    return {
        "index_exists": True,
        "index_path": str(index),
        "pages_missing_from_index": missing,
        "index_links_to_missing_pages": sorted(set(missing_targets)),
    }


def extract_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[1]
    return ""


def check_source_refs(root: Path, docs_dir: Path) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for page in md_pages(docs_dir):
        text = page.read_text(encoding="utf-8", errors="ignore")
        fm = extract_frontmatter(text)
        for line in fm.splitlines():
            match = FRONTMATTER_PATH_RE.match(line)
            if not match:
                continue
            raw_path = match.group(1).strip()
            if not raw_path or raw_path.startswith("http"):
                continue
            # Source refs may point to docs or source paths relative to repo root.
            target = (root / raw_path).resolve()
            if not target.exists():
                missing.append(
                    {
                        "page": str(page.relative_to(docs_dir)),
                        "source_ref": raw_path,
                    }
                )
    return missing


def read_state(docs_dir: Path) -> dict[str, Any] | None:
    for rel in ("_meta/state.json", "_meta/WIKI_STATE.json"):
        state_path = docs_dir / rel
        if not state_path.exists():
            continue
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            data.setdefault("_path", rel)
            return data
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "path": str(state_path)}
    return None


def checkpoint_changed_files(root: Path, state: dict[str, Any] | None) -> list[str]:
    if not state or not state.get("last_ingested_commit"):
        return []
    checkpoint = state["last_ingested_commit"]
    text = run(["git", "diff", "--name-only", f"{checkpoint}..HEAD"], cwd=root)
    if not text:
        return []
    return text.splitlines()


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    docs_dir = (root / args.docs_dir).resolve()
    state = read_state(docs_dir)
    report = {
        "repo_root": str(root),
        "docs_dir": str(docs_dir.relative_to(root))
        if docs_dir.exists()
        else args.docs_dir,
        "docs_exists": docs_dir.exists(),
        "markdown_pages": [str(p.relative_to(docs_dir)) for p in md_pages(docs_dir)]
        if docs_dir.exists()
        else [],
        "broken_links": check_links(docs_dir) if docs_dir.exists() else [],
        "index": check_index(docs_dir)
        if docs_dir.exists()
        else {"index_exists": False},
        "missing_source_refs": check_source_refs(root, docs_dir)
        if docs_dir.exists()
        else [],
        "wiki_state": state,
        "changed_files_since_checkpoint": checkpoint_changed_files(root, state),
    }
    report["summary"] = {
        "broken_link_count": len(report["broken_links"]),
        "pages_missing_from_index_count": len(
            report["index"].get("pages_missing_from_index", [])
        ),
        "index_missing_target_count": len(
            report["index"].get("index_links_to_missing_pages", [])
        ),
        "missing_source_ref_count": len(report["missing_source_refs"]),
        "changed_files_since_checkpoint_count": len(
            report["changed_files_since_checkpoint"]
        ),
    }
    return report


def as_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Docs Wiki Check")
    lines.append("")
    lines.append(f"- Repo root: `{report['repo_root']}`")
    lines.append(f"- Docs dir: `{report['docs_dir']}`")
    lines.append(f"- Docs exists: `{str(report['docs_exists']).lower()}`")
    lines.append(f"- Markdown pages: `{len(report.get('markdown_pages', []))}`")
    lines.append("")

    summary = report.get("summary", {})
    lines.append("## Summary")
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")

    lines.append("## Broken links")
    if report.get("broken_links"):
        for item in report["broken_links"][:100]:
            lines.append(f"- `{item['page']}` -> `{item['link']}`")
    else:
        lines.append("- None detected.")
    lines.append("")

    index = report.get("index", {})
    lines.append("## Index integrity")
    lines.append(f"- INDEX exists: `{str(index.get('index_exists')).lower()}`")
    missing = index.get("pages_missing_from_index", [])
    if missing:
        lines.append("- Pages missing from INDEX:")
        for page in missing[:100]:
            lines.append(f"  - `{page}`")
    else:
        lines.append("- No pages missing from INDEX detected.")
    targets = index.get("index_links_to_missing_pages", [])
    if targets:
        lines.append("- INDEX links to missing pages:")
        for target in targets[:100]:
            lines.append(f"  - `{target}`")
    lines.append("")

    lines.append("## Missing source refs")
    if report.get("missing_source_refs"):
        for item in report["missing_source_refs"][:100]:
            lines.append(
                f"- `{item['page']}` source ref missing: `{item['source_ref']}`"
            )
    else:
        lines.append("- None detected in page frontmatter.")
    lines.append("")

    changed = report.get("changed_files_since_checkpoint", [])
    lines.append("## Changed files since checkpoint")
    if changed:
        for path in changed[:100]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- None detected or no checkpoint available.")
    lines.append("")
    return "\n".join(lines)


def should_fail(report: dict[str, Any]) -> bool:
    summary = report.get("summary", {})
    return any(
        summary.get(key, 0) > 0
        for key in [
            "broken_link_count",
            "index_missing_target_count",
            "missing_source_ref_count",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check docs wiki health.")
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Docs directory relative to repo root. Default: docs",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument(
        "--strict", action="store_true", help="Exit nonzero for deterministic failures"
    )
    args = parser.parse_args()
    report = build_report(args)
    if args.format == "markdown":
        print(as_markdown(report))
    else:
        print(json.dumps(report, indent=2))
    return 1 if args.strict and should_fail(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
