from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
BIN_WRAPPER = ROOT / "bin" / "makerplace-validate"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
OPENCODE = ROOT / ".opencode"

TEXT_SUFFIXES = {
    ".json",
    ".js",
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
        CODEX_MARKETPLACE,
        ROOT / "opencode.json",
        ROOT / "docs" / "source-inventory.json",
        ROOT / "docs" / "source-provenance.json",
    ]
    files.extend(path / ".claude-plugin" / "plugin.json" for path in plugin_dirs())
    files.extend(path / ".codex-plugin" / "plugin.json" for path in plugin_dirs())
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


def validate_codex_manifests() -> None:
    marketplace = json.loads(CODEX_MARKETPLACE.read_text())
    if marketplace.get("name") != "claude-makerplace":
        fail("Codex marketplace name should be claude-makerplace")
    if marketplace.get("interface", {}).get("displayName") != "Claude Makerplace":
        fail("Codex marketplace display name should be Claude Makerplace")

    rows = marketplace.get("plugins")
    if not isinstance(rows, list):
        fail("Codex marketplace plugins should be a list")

    expected_names = {path.name for path in plugin_dirs()}
    declared_names = {row.get("name") for row in rows if isinstance(row, dict)}
    if declared_names != expected_names:
        fail("Codex marketplace plugin list does not match plugin directories")

    for row in rows:
        if not isinstance(row, dict):
            fail("Codex marketplace entries should be objects")
        name = row.get("name")
        source = row.get("source")
        if source != {"source": "local", "path": f"./plugins/{name}"}:
            fail(f"{name}: Codex marketplace source should point at ./plugins/{name}")
        policy = row.get("policy")
        if policy != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
            fail(f"{name}: Codex marketplace policy should use explicit defaults")
        if row.get("category") != "Developer Tools":
            fail(f"{name}: Codex marketplace category should be Developer Tools")

    for plugin in plugin_dirs():
        manifest_path = plugin / ".codex-plugin" / "plugin.json"
        if not manifest_path.exists():
            fail(f"{plugin}: missing Codex plugin manifest")
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("name") != plugin.name:
            fail(f"{plugin}: Codex manifest name does not match plugin directory")
        if sorted(manifest.get("keywords", [])) == []:
            fail(f"{plugin}: Codex manifest should include discovery keywords")

        skill_files = sorted((plugin / "skills").glob("*/SKILL.md"))
        if skill_files and manifest.get("skills") != "./skills/":
            fail(f"{plugin}: Codex skill plugin should expose ./skills/")
        if not skill_files and "skills" in manifest:
            fail(f"{plugin}: Codex manifest declares skills but no skill files exist")

    print("codex-manifests-ok")


def validate_opencode_adapter() -> None:
    if not (OPENCODE / "plugins" / "claude-makerplace.js").exists():
        fail("missing OpenCode runtime plugin")

    config = json.loads((ROOT / "opencode.json").read_text())
    if config.get("$schema") != "https://opencode.ai/config.json":
        fail("opencode.json should declare the OpenCode schema")
    if config.get("default_agent") != "makerplace-lead":
        fail("opencode.json should default to the makerplace-lead agent")

    skill_files = sorted(PLUGINS.glob("*/skills/*/SKILL.md"))
    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        link = OPENCODE / "skills" / skill_name
        if not link.exists():
            fail(f"OpenCode skill link missing for {skill_name}")
        if link.resolve() != skill_file.parent.resolve():
            fail(f"OpenCode skill link target mismatch for {skill_name}")

    command_files = sorted(PLUGINS.glob("*/commands/*.md"))
    for command_file in command_files:
        link = OPENCODE / "commands" / command_file.name
        if not link.exists():
            fail(f"OpenCode command link missing for {command_file.stem}")
        if link.resolve() != command_file.resolve():
            fail(f"OpenCode command link target mismatch for {command_file.stem}")

    expected_agents = {
        "makerplace-lead.md",
        "marketplace-auditor.md",
        "python-quality-reviewer.md",
        "skill-curator.md",
    }
    agent_files = sorted((OPENCODE / "agents").glob("*.md"))
    if {path.name for path in agent_files} != expected_agents:
        fail("OpenCode agent files do not match expected adapter agents")
    for path in agent_files:
        frontmatter = parse_frontmatter(path.read_text())
        if not frontmatter.get("description"):
            fail(f"{path}: OpenCode agent missing description")
        if frontmatter.get("mode") not in {"primary", "subagent"}:
            fail(f"{path}: OpenCode agent mode should be primary or subagent")

    print("opencode-adapter-ok")


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
        fail("runtime hooks are missing")
    for hook_file in hook_files:
        hooks = json.loads(hook_file.read_text())
        if "hooks" not in hooks:
            fail(f"{hook_file}: hooks object is missing")
        declared_events = set(hooks["hooks"])
        if not declared_events & {"PreToolUse", "PostToolUse", "Stop"}:
            fail(f"{hook_file}: no supported runtime hook events are declared")
        for event_name, entries in hooks["hooks"].items():
            if event_name not in {
                "PreToolUse",
                "PostToolUse",
                "SessionStart",
                "UserPromptSubmit",
                "Stop",
            }:
                fail(f"{hook_file}: unsupported hook event for Codex: {event_name}")
            if not isinstance(entries, list):
                fail(f"{hook_file}: {event_name} hook entries should be a list")
            for entry in entries:
                for hook in entry.get("hooks", []):
                    if hook.get("type") != "command":
                        fail(f"{hook_file}: {event_name} should use command hooks")
                    if not hook.get("command"):
                        fail(f"{hook_file}: {event_name} command is missing")

    python_hooks = json.loads(
        (PLUGINS / "python-quality" / "hooks" / "hooks.json").read_text()
    )["hooks"]
    post_tool_use = python_hooks.get("PostToolUse", [])
    stop = python_hooks.get("Stop", [])
    if (
        len(post_tool_use) != 1
        or post_tool_use[0].get("matcher") != "Write|Edit|MultiEdit"
    ):
        fail("python-quality PostToolUse hook should target Write|Edit|MultiEdit")
    if len(stop) != 1:
        fail("python-quality should declare one Stop hook for full quality checks")
    for event_name, entries in {"PostToolUse": post_tool_use, "Stop": stop}.items():
        command_hooks = [
            hook
            for entry in entries
            for hook in entry.get("hooks", [])
            if hook.get("type") == "command"
        ]
        if len(command_hooks) != 1:
            fail(f"python-quality {event_name} should declare one command hook")
        command = command_hooks[0].get("command", "")
        if "python-quality-hook.py" not in command:
            fail(f"python-quality {event_name} should run python-quality-hook.py")

    scripts = [
        PLUGINS / "makerplace-system" / "scripts" / "makerplace-guard.sh",
        PLUGINS / "makerplace-system" / "scripts" / "send-feedback.sh",
        PLUGINS / "python-quality" / "scripts" / "python-quality-hook.py",
        PLUGINS
        / "repository-documentation"
        / "scripts"
        / "repo-docs-wiki-stop-hook.py",
    ]
    for path in scripts:
        if not path.exists():
            fail(f"missing hook script: {path}")
    for path in scripts:
        mode = path.stat().st_mode
        if path.suffix == ".sh" and not mode & stat.S_IXUSR:
            fail(f"{path.name} is not executable")

    repo_docs_hooks_path = PLUGINS / "repository-documentation" / "hooks" / "hooks.json"
    if not repo_docs_hooks_path.exists():
        fail("repository-documentation should declare a repo-docs Stop hook")
    repo_docs_hooks = json.loads(repo_docs_hooks_path.read_text())["hooks"]
    repo_docs_stop = repo_docs_hooks.get("Stop", [])
    if len(repo_docs_stop) != 1:
        fail("repository-documentation should declare one Stop hook")
    repo_docs_command_hooks = [
        hook
        for entry in repo_docs_stop
        for hook in entry.get("hooks", [])
        if hook.get("type") == "command"
    ]
    if len(repo_docs_command_hooks) != 1:
        fail("repository-documentation Stop should declare one command hook")
    repo_docs_command = repo_docs_command_hooks[0].get("command", "")
    if "repo-docs-wiki-stop-hook.py" not in repo_docs_command:
        fail("repository-documentation Stop should run repo-docs-wiki-stop-hook.py")

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
        if ".git" in path.parts or "node_modules" in path.parts:
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
    payload = json.dumps(
        {"hook_event_name": "PostToolUse", "tool_input": {"file_path": str(target)}}
    )
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
    if "Python light quality hook ran" not in completed.stdout:
        fail("python quality PostToolUse hook did not report light checks")
    if "All Python light quality checks passed" not in completed.stdout:
        fail("python quality PostToolUse hook did not report passing checks")
    if "pytest" in completed.stdout:
        fail("python quality PostToolUse hook should not run pytest")

    with tempfile.TemporaryDirectory(prefix="makerplace-stop-hook-") as temp_name:
        temp = Path(temp_name)
        (temp / "sample.py").write_text(
            "def add(left: int, right: int) -> int:\n    return left + right\n"
        )
        tests = temp / "tests"
        tests.mkdir()
        (tests / "test_sample.py").write_text(
            "from sample import add\n\n\ndef test_add() -> None:\n    assert add(1, 2) == 3\n"
        )
        stop_payload = json.dumps(
            {
                "hook_event_name": "Stop",
                "cwd": str(temp),
                "stop_hook_active": False,
            }
        )
        stop_completed = subprocess.run(
            ["uv", "run", "python", str(target)],
            cwd=ROOT,
            input=stop_payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=240,
        )
    print(stop_completed.stdout.strip())
    if stop_completed.returncode != 0:
        fail("python quality Stop hook smoke test failed")
    if stop_completed.stdout.strip():
        fail("python quality Stop hook should be silent when full checks pass")
    print("python-hook-smoke-ok")


def repo_docs_page(title: str, typ: str, summary: str) -> str:
    return f"""---
title: {title}
type: {typ}
summary: {summary}
tags: [docs-wiki]
source_refs: []
status: draft
updated: 2026-01-01
---

# {title}

{summary}
"""


def run_repo_docs_hook_smoke() -> None:
    target = (
        PLUGINS / "repository-documentation" / "scripts" / "repo-docs-wiki-stop-hook.py"
    )
    with tempfile.TemporaryDirectory(prefix="makerplace-repo-docs-hook-") as temp_name:
        temp = Path(temp_name)
        subprocess.run(
            ["git", "init", "-q"],
            cwd=temp,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
            check=True,
        )
        docs = temp / "docs"
        (docs / "_meta").mkdir(parents=True)
        (docs / "architecture").mkdir()
        (docs / "_meta" / "schema.md").write_text(
            repo_docs_page(
                "Repo Docs Wiki Schema",
                "meta",
                "Defines the local docs-wiki conventions.",
            ),
            encoding="utf-8",
        )
        (docs / "_meta" / "log.md").write_text(
            repo_docs_page(
                "Repo Docs Wiki Log",
                "meta",
                "Records docs-wiki maintenance events.",
            ),
            encoding="utf-8",
        )
        (docs / "index.md").write_text(
            repo_docs_page(
                "Documentation Index",
                "index",
                "Catalog of the repository documentation wiki.",
            ),
            encoding="utf-8",
        )
        (docs / "architecture" / "overview.md").write_text(
            repo_docs_page(
                "Architecture Overview",
                "architecture",
                "Describes the system architecture.",
            ),
            encoding="utf-8",
        )

        payload = json.dumps(
            {
                "hook_event_name": "Stop",
                "cwd": str(temp),
                "stop_hook_active": False,
            }
        )
        completed = subprocess.run(
            ["uv", "run", "python", str(target)],
            cwd=ROOT,
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=240,
        )
        print(completed.stdout.strip())
        if completed.returncode != 0:
            fail("repo docs Stop hook smoke test failed")
        output = completed.stdout.strip()
        if "Repo docs wiki Stop hook ran" not in output:
            fail("repo docs Stop hook should report changed docs work")
        index = (docs / "index.md").read_text(encoding="utf-8")
        if "architecture/overview.md" not in index:
            fail("repo docs Stop hook should refresh docs/index.md")
        if '"decision": "block"' in output:
            fail("repo docs Stop hook should not block a valid docs wiki")
    print("repo-docs-hook-smoke-ok")


def run_feedback_sender_smoke() -> None:
    target = PLUGINS / "makerplace-system" / "scripts" / "send-feedback.sh"
    completed = subprocess.run(
        [str(target), "-"],
        cwd=ROOT,
        input='{"message":"feedback smoke"}',
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    print(completed.stdout.strip())
    if completed.returncode != 1:
        fail("feedback sender should fail without a configured destination")
    if completed.stdout.strip() != "FAIL:missing-destination":
        fail(
            "feedback sender should report missing destination without leaking details"
        )

    github_env = {
        **os.environ,
        "MAKERPLACE_FEEDBACK_DESTINATION": "github",
        "MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY": "owner/repo",
        "MAKERPLACE_FEEDBACK_GITHUB_TOKEN": "dry-run-token",
        "MAKERPLACE_FEEDBACK_DRY_RUN": "1",
    }
    github_issue = subprocess.run(
        [str(target), "-"],
        cwd=ROOT,
        env=github_env,
        input='{"message":"feedback smoke"}',
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    print(github_issue.stdout.strip())
    if (
        github_issue.returncode != 0
        or github_issue.stdout.strip() != "DRYRUN:github-issue"
    ):
        fail("feedback sender should support GitHub issue dry run")

    github_comment_env = {
        **github_env,
        "MAKERPLACE_FEEDBACK_GITHUB_ISSUE_NUMBER": "1",
    }
    github_comment = subprocess.run(
        [str(target), "-"],
        cwd=ROOT,
        env=github_comment_env,
        input='{"message":"feedback smoke"}',
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    print(github_comment.stdout.strip())
    if (
        github_comment.returncode != 0
        or github_comment.stdout.strip() != "DRYRUN:github-comment"
    ):
        fail("feedback sender should support GitHub issue comment dry run")
    print("feedback-sender-smoke-ok")


def main() -> int:
    validate_json()
    validate_plugin_manifest_conventions()
    validate_codex_manifests()
    validate_opencode_adapter()
    validate_skills()
    validate_commands()
    validate_agents()
    validate_selection_map()
    validate_hooks()
    validate_bin_wrapper()
    validate_no_leaks()
    run_claude_validation_if_available()
    run_python_hook_smoke()
    run_repo_docs_hook_smoke()
    run_feedback_sender_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
