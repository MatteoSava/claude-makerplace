#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "assets" / "project_scaffold"


def copy_tree(src: Path, dst: Path, force: bool = False) -> None:
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        out = dst / rel
        if item.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and not force:
            continue
        shutil.copy2(item, out)


def append_once(path: Path, snippet: str, marker: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in existing:
        return
    with path.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(f"\n<!-- {marker} -->\n")
        f.write(snippet.strip() + "\n")


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
    return frontmatter, text[end + 4 :].strip()


def write_opencode_agent(src: Path, dst: Path, force: bool = False) -> None:
    frontmatter, body = parse_frontmatter(src.read_text(encoding="utf-8"))
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "---",
            f"description: {frontmatter.get('description', src.stem)}",
            "mode: subagent",
            "permission:",
            "  edit: ask",
            "  read: allow",
            "  list: allow",
            "  grep: allow",
            "  glob: allow",
            "  bash:",
            '    "*": ask',
            "  skill:",
            '    "*": allow',
            "---",
            "",
            body,
            "",
        ]
    )
    dst.write_text(text, encoding="utf-8")


def install_opencode(target: Path, force: bool = False) -> None:
    skill_target = target / ".opencode" / "skills" / "agentops-continuity" / "SKILL.md"
    skill_target.parent.mkdir(parents=True, exist_ok=True)
    if not skill_target.exists() or force:
        shutil.copy2(ROOT / "SKILL.md", skill_target)

    for agent in sorted((ROOT / "agents").glob("*.md")):
        write_opencode_agent(
            agent,
            target / ".opencode" / "agents" / agent.name,
            force=force,
        )

    config_target = target / ".opencode" / "opencode.agentops-continuity.example.json"
    if not config_target.exists() or force:
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


def main() -> int:
    p = argparse.ArgumentParser(
        description="Install AgentOps Continuity into a repository"
    )
    p.add_argument("--target", default=".", help="Repository root")
    p.add_argument("--claude", action="store_true", help="Install Claude Code scaffold")
    p.add_argument("--codex", action="store_true", help="Install Codex scaffold")
    p.add_argument("--opencode", action="store_true", help="Install OpenCode scaffold")
    p.add_argument(
        "--append-agents", action="store_true", help="Append AGENTS.md snippet"
    )
    p.add_argument(
        "--append-claude", action="store_true", help="Append CLAUDE.md snippet"
    )
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = p.parse_args()

    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    any_adapter = args.claude or args.codex or args.opencode

    # Always install core state/script/policy.
    for rel in [".agentops-continuity"]:
        copy_tree(SCAFFOLD / rel, target / rel, force=args.force)

    if args.claude or not any_adapter:
        copy_tree(SCAFFOLD / ".claude", target / ".claude", force=args.force)
    if args.codex or not any_adapter:
        copy_tree(SCAFFOLD / ".codex", target / ".codex", force=args.force)
        copy_tree(SCAFFOLD / ".agents", target / ".agents", force=args.force)
        shutil.copy2(
            SCAFFOLD / "AGENTS.agentops-continuity.md",
            target / "AGENTS.agentops-continuity.md",
        )
    if args.claude or not any_adapter:
        shutil.copy2(
            SCAFFOLD / "CLAUDE.agentops-continuity.md",
            target / "CLAUDE.agentops-continuity.md",
        )
    if args.opencode or not any_adapter:
        install_opencode(target, force=args.force)

    if args.append_agents:
        snippet = (SCAFFOLD / "AGENTS.agentops-continuity.md").read_text(
            encoding="utf-8"
        )
        append_once(target / "AGENTS.md", snippet, "agentops-continuity")
    if args.append_claude:
        snippet = (SCAFFOLD / "CLAUDE.agentops-continuity.md").read_text(
            encoding="utf-8"
        )
        append_once(target / "CLAUDE.md", snippet, "agentops-continuity")

    print(f"Installed AgentOps Continuity scaffold into {target}")
    print("Core: .agentops-continuity/agentops_continuity.py")
    if args.claude:
        print("Claude example hooks: .claude/settings.agentops-continuity.example.json")
    if args.codex:
        print("Codex hooks: .codex/hooks.json")
    if args.opencode or not any_adapter:
        print(
            "OpenCode skill and agents: .opencode/skills/agentops-continuity and .opencode/agents"
        )
    print("Run: python .agentops-continuity/agentops_continuity.py doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
