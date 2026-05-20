from __future__ import annotations

import json
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
BIN_WRAPPER = ROOT / "bin" / "makerplace-validate"

TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".sh",
    ".yml",
    ".yaml",
    ".toml",
}

SENSITIVE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        "Mat" + "teo",
        "So" + "gei",
        "Canali" + "Telegram",
        "Re" + "ply",
        "Ba" + "roots",
        "ya" + "saf",
        "So" + "gei1Collection",
        "ALM" + "-DevOps",
        "portale" + "-ms-chatbot",
        r"192[.]168",
        "user" + "@example",
        "AA" + ":BB",
        "aaron" + "-he-zhu",
        "dev[.]" + "azure[.]com",
        "Lang" + "fuse",
        r"exp-[0-9]",
        "public" + "_lev",
        "/" + "Users/",
    )
]


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(
    command: list[str], cwd: Path = ROOT, timeout: int = 120
) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if completed.stdout:
        print(completed.stdout.strip())
    if completed.returncode != 0:
        fail(
            f"command failed with exit code {completed.returncode}: {' '.join(command)}"
        )
    return completed


def plugin_dirs() -> list[Path]:
    return sorted(
        path
        for path in PLUGINS.iterdir()
        if path.is_dir() and (path / ".claude-plugin" / "plugin.json").exists()
    )


def validate_json() -> None:
    files = [
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / "docs" / "source-inventory.json",
        ROOT / "docs" / "source-provenance.json",
    ]
    files.extend(path / ".claude-plugin" / "plugin.json" for path in plugin_dirs())
    files.extend(sorted(PLUGINS.glob("*/hooks/hooks.json")))
    files.extend(sorted(PLUGINS.glob("*/.lsp.json")))
    for path in files:
        with path.open() as handle:
            json.load(handle)
    print(f"json-ok: {len(files)} files")


def validate_plugin_manifest_conventions() -> None:
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    if marketplace.get("name") != "claude-makerplace":
        fail("marketplace name should be claude-makerplace")

    marketplace_plugins = marketplace.get("plugins")
    if not isinstance(marketplace_plugins, list) or len(marketplace_plugins) < 2:
        fail("marketplace should publish multiple organized plugins")

    expected_sources = {f"./plugins/{path.name}" for path in plugin_dirs()}
    declared_sources = {
        row.get("source") for row in marketplace_plugins if isinstance(row, dict)
    }
    if declared_sources != expected_sources:
        fail("marketplace plugin list does not match plugin directories")

    for plugin in plugin_dirs():
        manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
        if manifest.get("name") != plugin.name:
            fail(f"{plugin}: manifest name does not match plugin directory")
        if "hooks" in manifest:
            fail(
                f"{plugin}: plugin.json should not declare hooks explicitly; keep "
                "hooks/hooks.json auto-discovered to avoid duplicate hook loading"
            )
        lsp_config = plugin / ".lsp.json"
        if lsp_config.exists() and manifest.get("lspServers") != "./.lsp.json":
            fail(f"{plugin}: LSP config should be exposed with ./.lsp.json")
        if not lsp_config.exists() and "lspServers" in manifest:
            fail(f"{plugin}: lspServers declared but .lsp.json does not exist")

        command_files = sorted((plugin / "commands").glob("*.md"))
        if command_files and manifest.get("commands") != "./commands":
            fail(f"{plugin}: command plugin should expose ./commands")
        if not command_files and "commands" in manifest:
            fail(f"{plugin}: commands declared but no command files exist")

        agent_files = sorted((plugin / "agents").glob("*.md"))
        expected_agents = [f"./agents/{path.name}" for path in agent_files]
        if agent_files and manifest.get("agents") != expected_agents:
            fail(f"{plugin}: agent list should match explicit agent files")
        if not agent_files and "agents" in manifest:
            fail(f"{plugin}: agents declared but no agent files exist")

    print("plugin-manifest-conventions-ok")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}

    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "-")):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def validate_skills() -> None:
    skill_files = sorted(PLUGINS.glob("*/skills/*/SKILL.md"))
    if not skill_files:
        fail("no skills found")

    seen: set[str] = set()
    for path in skill_files:
        text = path.read_text()
        frontmatter = parse_frontmatter(text)
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if not name:
            fail(f"{path}: missing frontmatter name")
        if name != path.parent.name:
            fail(f"{path}: frontmatter name does not match directory")
        if name in seen:
            fail(f"duplicate skill name: {name}")
        if not description:
            fail(f"{path}: missing frontmatter description")
        if not re.fullmatch(r"[a-z0-9-]+", name):
            fail(f"{path}: invalid skill name {name!r}")
        seen.add(name)

    readme = (ROOT / "README.md").read_text()
    match = re.search(r"contains (\d+) skills", readme)
    if not match:
        fail("README does not state published skill count")
    expected_count = int(match.group(1))
    if expected_count != len(skill_files):
        fail(
            f"README skill count {expected_count} does not match actual count {len(skill_files)}"
        )

    print(f"skills-ok: {len(skill_files)} skills")


def validate_commands() -> None:
    command_files = sorted(PLUGINS.glob("*/commands/*.md"))
    if len(command_files) < 3:
        fail("expected at least 3 command files")

    seen: set[str] = set()
    for path in command_files:
        text = path.read_text()
        frontmatter = parse_frontmatter(text)
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if not name:
            fail(f"{path}: missing frontmatter name")
        if name != path.stem:
            fail(f"{path}: frontmatter name does not match filename")
        if name in seen:
            fail(f"duplicate command name: {name}")
        if not description:
            fail(f"{path}: missing frontmatter description")
        if not re.fullmatch(r"[a-z0-9-]+", name):
            fail(f"{path}: invalid command name {name!r}")
        seen.add(name)

    print(f"commands-ok: {len(command_files)} commands")


def validate_agents() -> None:
    agent_files = sorted(PLUGINS.glob("*/agents/*.md"))
    if len(agent_files) < 3:
        fail("expected at least 3 agent files")

    unsupported_fields = {"hooks", "mcpServers", "permissionMode"}
    seen: set[str] = set()
    for path in agent_files:
        text = path.read_text()
        frontmatter = parse_frontmatter(text)
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if not name:
            fail(f"{path}: missing frontmatter name")
        if name != path.stem:
            fail(f"{path}: frontmatter name does not match filename")
        if name in seen:
            fail(f"duplicate agent name: {name}")
        if not description:
            fail(f"{path}: missing frontmatter description")
        if not re.fullmatch(r"[a-z0-9-]+", name):
            fail(f"{path}: invalid agent name {name!r}")
        found_unsupported = sorted(unsupported_fields & set(frontmatter))
        if found_unsupported:
            fail(
                f"{path}: plugin agents cannot rely on unsupported fields: "
                + ", ".join(found_unsupported)
            )
        seen.add(name)

    print(f"agents-ok: {len(agent_files)} agents")


def validate_selection_map() -> None:
    inventory = json.loads((ROOT / "docs" / "source-inventory.json").read_text())
    candidates = {row["name"] for row in inventory if row["decision"] == "candidate"}
    selection_map = (ROOT / "docs" / "selection-map.md").read_text()
    missing = sorted(
        candidate for candidate in candidates if f"`{candidate}`" not in selection_map
    )
    if missing:
        fail(f"selection map missing candidates: {', '.join(missing)}")
    print(f"selection-map-ok: {len(candidates)} candidates covered")


def validate_hooks() -> None:
    hook_files = sorted(PLUGINS.glob("*/hooks/hooks.json"))
    if not hook_files:
        fail("PostToolUse hooks are missing")
    for hook_file in hook_files:
        hooks = json.loads(hook_file.read_text())
        if "hooks" not in hooks or "PostToolUse" not in hooks["hooks"]:
            fail(f"{hook_file}: PostToolUse hooks are missing")

    scripts = [
        PLUGINS / "makerplace-system" / "scripts" / "makerplace-guard.sh",
        PLUGINS / "python-quality" / "scripts" / "python-quality-hook.py",
    ]
    for path in scripts:
        if not path.exists():
            fail(f"missing hook script: {path}")
    for path in scripts:
        mode = path.stat().st_mode
        if path.suffix == ".sh" and not mode & stat.S_IXUSR:
            fail(f"{path.name} is not executable")

    print("hooks-ok")


def validate_bin_wrapper() -> None:
    if not BIN_WRAPPER.exists():
        fail("missing bin/makerplace-validate")
    mode = BIN_WRAPPER.stat().st_mode
    if not mode & stat.S_IXUSR:
        fail("bin/makerplace-validate is not executable")

    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text()
    if "./bin/makerplace-validate" not in workflow:
        fail("CI workflow should call ./bin/makerplace-validate")

    print("bin-wrapper-ok")


def validate_no_leaks() -> None:
    violations: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(errors="replace")
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {pattern.pattern}")

    if violations:
        fail("sensitive markers found:\n" + "\n".join(violations[:50]))
    print("leak-scan-ok")


def run_claude_validation_if_available() -> None:
    if not shutil.which("claude"):
        print("claude-cli-skip: claude executable not available")
        return
    run(["claude", "plugin", "validate", "."])
    for plugin in plugin_dirs():
        run(["claude", "plugin", "validate", str(plugin.relative_to(ROOT))])


def run_python_hook_smoke() -> None:
    target = PLUGINS / "python-quality" / "scripts" / "python-quality-hook.py"
    payload = json.dumps({"tool_input": {"file_path": str(target)}})
    completed = subprocess.run(
        ["uv", "run", "python", str(target)],
        cwd=ROOT,
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    print(completed.stdout.strip())
    if completed.returncode != 0:
        fail("python quality hook smoke test failed")
    if "All Python quality checks passed" not in completed.stdout:
        fail("python quality hook did not report passing checks")
    print("python-hook-smoke-ok")


def main() -> int:
    validate_json()
    validate_plugin_manifest_conventions()
    validate_skills()
    validate_commands()
    validate_agents()
    validate_selection_map()
    validate_hooks()
    validate_bin_wrapper()
    validate_no_leaks()
    run_claude_validation_if_available()
    run_python_hook_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
