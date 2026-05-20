#!/usr/bin/env python3
"""Install the webqa-devtools project scaffold into a repository."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "assets" / "project_scaffold"


def copy_tree(src: Path, dst: Path, force: bool = False) -> list[str]:
    copied: list[str] = []
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and not force:
            example = (
                out.with_suffix(out.suffix + ".example")
                if out.suffix
                else out.with_name(out.name + ".example")
            )
            shutil.copy2(item, example)
            copied.append(f"kept existing {rel}; wrote {example.relative_to(dst)}")
        else:
            shutil.copy2(item, out)
            copied.append(str(rel))
    return copied


def append_once(path: Path, marker: str, text: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in existing:
        return False
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + "\n" + text.strip() + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install webqa-devtools scaffold into a repository"
    )
    parser.add_argument("--target", default=".", help="Repository root to install into")
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Install Claude Code example settings and instructions",
    )
    parser.add_argument(
        "--codex",
        action="store_true",
        help="Install Codex hooks, skill, and MCP config snippets",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files instead of writing .example copies",
    )
    parser.add_argument(
        "--append-agents",
        action="store_true",
        help="Append webqa-devtools snippet to AGENTS.md",
    )
    parser.add_argument(
        "--append-claude",
        action="store_true",
        help="Append webqa-devtools snippet to CLAUDE.md",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)

    if not SCAFFOLD.exists():
        raise SystemExit(f"Missing scaffold directory: {SCAFFOLD}")

    # Always copy shared core.
    shared = [".webqa-devtools"]
    if args.claude:
        shared.append(".claude")
        shared.append("CLAUDE.repo-webqa-devtools.md")
    if args.codex:
        shared.extend([".codex", ".agents", "AGENTS.repo-webqa-devtools.md"])
    if not args.claude and not args.codex:
        shared.extend(
            [
                ".claude",
                ".codex",
                ".agents",
                "AGENTS.repo-webqa-devtools.md",
                "CLAUDE.repo-webqa-devtools.md",
            ]
        )

    copied: list[str] = []
    for name in shared:
        src = SCAFFOLD / name
        if not src.exists():
            continue
        if src.is_dir():
            copied.extend(copy_tree(src, target / name, args.force))
        else:
            out = target / name
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists() and not args.force:
                example = (
                    out.with_suffix(out.suffix + ".example")
                    if out.suffix
                    else out.with_name(out.name + ".example")
                )
                shutil.copy2(src, example)
                copied.append(f"kept existing {name}; wrote {example.name}")
            else:
                shutil.copy2(src, out)
                copied.append(name)

    if args.append_agents:
        snippet = (SCAFFOLD / "AGENTS.repo-webqa-devtools.md").read_text(
            encoding="utf-8"
        )
        changed = append_once(
            target / "AGENTS.md", "WEBQA-DEVTOOLS-INSTRUCTIONS", snippet
        )
        copied.append(
            "updated AGENTS.md" if changed else "AGENTS.md already contained snippet"
        )

    if args.append_claude:
        snippet = (SCAFFOLD / "CLAUDE.repo-webqa-devtools.md").read_text(
            encoding="utf-8"
        )
        changed = append_once(
            target / "CLAUDE.md", "WEBQA-DEVTOOLS-INSTRUCTIONS", snippet
        )
        copied.append(
            "updated CLAUDE.md" if changed else "CLAUDE.md already contained snippet"
        )

    print("Installed webqa-devtools scaffold into", target)
    for item in copied:
        print("-", item)
    print("\nNext steps:")
    if args.claude or not (args.claude or args.codex):
        print(
            "- Merge .claude/settings.webqa-devtools.example.json into .claude/settings.json"
        )
        print(
            "- Connect MCP: claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest"
        )
    if args.codex or not (args.claude or args.codex):
        print(
            "- Connect MCP: codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest"
        )
        print(
            "- Merge .codex/config.webqa-devtools.example.toml if your Codex setup uses config.toml"
        )
    print("- Run: python .webqa-devtools/webqa_devtools.py preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
