#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = PACKAGE_ROOT / "assets" / "project_scaffold"


def copy_path(src: Path, dst: Path, overwrite: bool = False) -> None:
    if src.name == "__pycache__" or src.suffix in {".pyc", ".pyo"}:
        return
    if src.is_dir():
        for child in src.iterdir():
            copy_path(child, dst / child.name, overwrite)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        print(f"skip existing: {dst}")
        return
    shutil.copy2(src, dst)
    print(f"wrote: {dst}")


def merge_json_hooks(example: Path, target: Path, overwrite: bool = False) -> None:
    if not example.exists():
        return
    src = json.loads(example.read_text(encoding="utf-8"))
    if target.exists():
        dst = json.loads(target.read_text(encoding="utf-8"))
    else:
        dst = {}
    dst.setdefault("hooks", {})
    for event, groups in src.get("hooks", {}).items():
        dst["hooks"].setdefault(event, [])
        existing = json.dumps(dst["hooks"][event], sort_keys=True)
        for group in groups:
            encoded = json.dumps(group, sort_keys=True)
            if encoded not in existing:
                dst["hooks"][event].append(group)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        backup = target.with_suffix(target.suffix + ".repo-sentinel.bak")
        shutil.copy2(target, backup)
        print(f"backup: {backup}")
    target.write_text(
        json.dumps(dst, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"merged hooks: {target}")


def append_snippet(
    snippet: Path, target: Path, marker: str, overwrite: bool = False
) -> None:
    text = snippet.read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        current = target.read_text(encoding="utf-8")
        if marker in current and not overwrite:
            print(f"skip snippet already present: {target}")
            return
        new = current.rstrip() + "\n\n" + marker + "\n" + text + "\n"
    else:
        new = marker + "\n" + text + "\n"
    target.write_text(new, encoding="utf-8")
    print(f"updated: {target}")


def install_opencode(target: Path, overwrite: bool = False) -> None:
    skill_target = target / ".opencode" / "skills" / "repo-sentinel" / "SKILL.md"
    copy_path(PACKAGE_ROOT / "SKILL.md", skill_target, overwrite)
    config_target = target / ".opencode" / "opencode.repo-sentinel.example.json"
    if config_target.exists() and not overwrite:
        print(f"skip existing: {config_target}")
        return
    config_target.parent.mkdir(parents=True, exist_ok=True)
    config_target.write_text(
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "permission": {"skill": {"*": "allow"}},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote: {config_target}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install Repo Sentinel scaffold into a repository"
    )
    parser.add_argument("--target", default=".", help="Target repository root")
    parser.add_argument(
        "--claude", action="store_true", help="Install Claude Code example hooks"
    )
    parser.add_argument(
        "--codex", action="store_true", help="Install Codex hooks, rules, and skill"
    )
    parser.add_argument(
        "--opencode", action="store_true", help="Install OpenCode skill scaffold"
    )
    parser.add_argument(
        "--merge-claude",
        action="store_true",
        help="Merge Claude hook example into .claude/settings.json",
    )
    parser.add_argument(
        "--append-agents",
        action="store_true",
        help="Append Repo Sentinel section to AGENTS.md",
    )
    parser.add_argument(
        "--append-claude",
        action="store_true",
        help="Append Repo Sentinel section to CLAUDE.md",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing scaffold files"
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    any_adapter = args.claude or args.codex or args.opencode

    # Always install the core.
    copy_path(SCAFFOLD / ".repo-sentinel", target / ".repo-sentinel", args.overwrite)

    if args.claude or not any_adapter:
        copy_path(SCAFFOLD / ".claude", target / ".claude", args.overwrite)
        if args.merge_claude:
            merge_json_hooks(
                target / ".claude/settings.repo-sentinel.example.json",
                target / ".claude/settings.json",
                args.overwrite,
            )
        copy_path(
            SCAFFOLD / "CLAUDE.repo-sentinel.md",
            target / "CLAUDE.repo-sentinel.md",
            args.overwrite,
        )

    if args.codex or not any_adapter:
        copy_path(SCAFFOLD / ".codex", target / ".codex", args.overwrite)
        copy_path(SCAFFOLD / ".agents", target / ".agents", args.overwrite)
        copy_path(
            SCAFFOLD / "AGENTS.repo-sentinel.md",
            target / "AGENTS.repo-sentinel.md",
            args.overwrite,
        )
    if args.opencode or not any_adapter:
        install_opencode(target, args.overwrite)

    if args.append_agents:
        append_snippet(
            SCAFFOLD / "AGENTS.repo-sentinel.md",
            target / "AGENTS.md",
            "<!-- repo-sentinel:start -->",
            args.overwrite,
        )
    if args.append_claude:
        append_snippet(
            SCAFFOLD / "CLAUDE.repo-sentinel.md",
            target / "CLAUDE.md",
            "<!-- repo-sentinel:start -->",
            args.overwrite,
        )

    print(
        "\nRepo Sentinel scaffold installed. Review files before trusting/enabling hooks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
