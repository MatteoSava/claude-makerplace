#!/usr/bin/env python3
"""Install the webqa-devtools project scaffold into a repository."""

from __future__ import annotations

import argparse
import json
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


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text.strip()
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text.strip()
    frontmatter: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    body = text[end + 4 :].strip()
    return frontmatter, body


def opencode_permission_for_tools(tools: str) -> str:
    names = {item.strip().lower() for item in tools.split(",")}
    lines = ["permission:", "  edit: deny"]
    if "read" in names:
        lines.append("  read: allow")
        lines.append("  list: allow")
    if "grep" in names:
        lines.append("  grep: allow")
    if "glob" in names:
        lines.append("  glob: allow")
    if "bash" in names:
        lines.append("  bash:")
        lines.append('    "*": ask')
    return "\n".join(lines)


def write_opencode_agent(src: Path, dst: Path, force: bool = False) -> None:
    frontmatter, body = parse_frontmatter(src.read_text(encoding="utf-8"))
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    permission = opencode_permission_for_tools(frontmatter.get("tools", "Read"))
    text = "\n".join(
        [
            "---",
            f"description: {frontmatter.get('description', src.stem)}",
            "mode: subagent",
            permission,
            "---",
            "",
            body,
            "",
        ]
    )
    dst.write_text(text, encoding="utf-8")


def install_opencode(target: Path, force: bool = False) -> list[str]:
    copied: list[str] = []
    skill_target = target / ".opencode" / "skills" / "webqa-devtools" / "SKILL.md"
    skill_target.parent.mkdir(parents=True, exist_ok=True)
    if not skill_target.exists() or force:
        shutil.copy2(ROOT / "SKILL.md", skill_target)
        copied.append(".opencode/skills/webqa-devtools/SKILL.md")

    for agent in sorted((ROOT / "agents").glob("*.md")):
        out = target / ".opencode" / "agents" / agent.name
        write_opencode_agent(agent, out, force)
        copied.append(f".opencode/agents/{agent.name}")

    config = {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {
            "chrome-devtools": {
                "type": "local",
                "command": [
                    "npx",
                    "-y",
                    "chrome-devtools-mcp@latest",
                    "--isolated",
                ],
                "enabled": True,
                "timeout": 20000,
            }
        },
        "permission": {"skill": {"*": "allow"}},
    }
    config_target = target / ".opencode" / "opencode.webqa-devtools.example.json"
    if not config_target.exists() or force:
        config_target.parent.mkdir(parents=True, exist_ok=True)
        config_target.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        copied.append(".opencode/opencode.webqa-devtools.example.json")
    return copied


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
        "--opencode",
        action="store_true",
        help="Install OpenCode skill, agents, and MCP config example",
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
    any_adapter = args.claude or args.codex or args.opencode
    shared = [".webqa-devtools"]
    if args.claude:
        shared.append(".claude")
        shared.append("CLAUDE.repo-webqa-devtools.md")
    if args.codex:
        shared.extend([".codex", ".agents", "AGENTS.repo-webqa-devtools.md"])
    if not any_adapter:
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

    if args.opencode or not any_adapter:
        copied.extend(install_opencode(target, args.force))

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
    if args.claude or not any_adapter:
        print(
            "- Merge .claude/settings.webqa-devtools.example.json into .claude/settings.json"
        )
        print(
            "- Connect MCP: claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest"
        )
    if args.codex or not any_adapter:
        print(
            "- Connect MCP: codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest"
        )
        print(
            "- Merge .codex/config.webqa-devtools.example.toml if your Codex setup uses config.toml"
        )
    if args.opencode or not any_adapter:
        print(
            "- Merge .opencode/opencode.webqa-devtools.example.json into opencode.json or .opencode/opencode.json"
        )
        print("- Restart OpenCode, then run: opencode debug skill")
    print("- Run: python .webqa-devtools/webqa_devtools.py preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
