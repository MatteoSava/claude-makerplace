from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def hooks_disabled() -> bool:
    return os.environ.get("MAKERPLACE_HOOKS", "on").lower() in {
        "0",
        "false",
        "off",
        "disabled",
    }


def read_payload() -> dict[str, object]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def hook_event_name(payload: dict[str, object]) -> str:
    value = payload.get("hook_event_name")
    return value if isinstance(value, str) else "Stop"


def stop_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def hook_output(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": message,
                }
            }
        )
    )


def repo_root(start: Path) -> Path:
    current = start.parent if start.is_file() else start
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=current,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        completed = None
    if completed and completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip()).resolve()

    markers = ("docs", "pyproject.toml", "package.json", ".git")
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in markers):
            return candidate.resolve()
    return current.resolve()


def project_root_from_payload(payload: dict[str, object]) -> Path:
    candidates = [
        payload.get("cwd"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.getcwd(),
    ]
    for value in candidates:
        if isinstance(value, str) and value:
            path = Path(value).expanduser()
            if path.exists():
                return repo_root(path.resolve())
    return repo_root(Path.cwd())


def skill_scripts_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / "repo-docs-wiki" / "scripts"


def run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 120,
) -> tuple[int, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(cwd) if not pythonpath else f"{cwd}{os.pathsep}{pythonpath}"
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, str(exc)
    except subprocess.TimeoutExpired as exc:
        output_text = exc.stdout if isinstance(exc.stdout, str) else ""
        return 124, f"{output_text}\nTimed out after {timeout}s".strip()
    return completed.returncode, completed.stdout.strip()


def changed_docs_files(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    commands = [
        ["git", "diff", "--name-only", "--", "docs"],
        ["git", "diff", "--name-only", "--cached", "--", "docs"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "docs"],
    ]
    changed: list[str] = []
    seen: set[str] = set()
    for command in commands:
        code, output = run_command(command, cwd=root, timeout=30)
        if code != 0:
            continue
        for line in output.splitlines():
            path = line.strip()
            if path and path not in seen:
                changed.append(path)
                seen.add(path)
    return changed


def is_docs_wiki(root: Path) -> bool:
    schema = root / "docs" / "_meta" / "schema.md"
    if not schema.exists():
        return False
    text = schema.read_text(encoding="utf-8", errors="replace")
    return "docs-wiki" in text or "Repo Docs Wiki" in text


def has_markdown_pages(root: Path) -> bool:
    docs = root / "docs"
    if not docs.exists():
        return False
    for path in docs.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.relative_to(docs).parts):
            continue
        if path.name != "index.md":
            return True
    return False


def should_update_index(root: Path, changed_files: list[str]) -> bool:
    if not changed_files:
        return False
    docs = root / "docs"
    if not has_markdown_pages(root):
        return False
    index = docs / "index.md"
    if not index.exists():
        return True
    text = index.read_text(encoding="utf-8", errors="replace")
    return "docs-wiki" in text or "Documentation Index" in text


def trim_output(output: str, *, max_lines: int = 40) -> str:
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return output
    return "\n".join(["... output truncated ...", *lines[-max_lines:]])


def run_repo_docs_stop(payload: dict[str, object]) -> int:
    if payload.get("stop_hook_active") is True:
        return 0

    root = project_root_from_payload(payload)
    docs = root / "docs"
    if not docs.exists() or not is_docs_wiki(root):
        return 0

    changed_files = changed_docs_files(root)
    if not changed_files:
        return 0

    scripts = skill_scripts_dir()
    commands: list[tuple[str, list[str], int, bool]] = []
    if should_update_index(root, changed_files):
        commands.append(
            (
                "update docs index",
                ["uv", "run", "python", str(scripts / "update_docs_index.py"), "docs"],
                120,
                True,
            )
        )
    commands.extend(
        [
            (
                "docs wiki lint",
                ["uv", "run", "python", str(scripts / "docs_wiki_lint.py"), "docs"],
                120,
                True,
            ),
            (
                "docs wiki check",
                [
                    "uv",
                    "run",
                    "python",
                    str(scripts / "check_docs_wiki.py"),
                    "--strict",
                    "--format",
                    "markdown",
                ],
                120,
                True,
            ),
        ]
    )

    summaries: list[str] = []
    failures: list[str] = []
    for label, command, timeout, blocking in commands:
        code, output = run_command(command, cwd=root, timeout=timeout)
        status = "PASS" if code == 0 else f"FAIL {code}"
        summary = f"- {label}: {status}"
        if output:
            summary += f"\n```text\n{trim_output(output)}\n```"
        summaries.append(summary)
        if code != 0 and blocking:
            failures.append(summary)

    changed_display = "\n".join(f"- `{path}`" for path in changed_files[:30])
    header = (
        f"Repo docs wiki Stop hook ran because docs files changed:\n{changed_display}"
    )
    body = "\n\n".join(summaries)
    if failures:
        stop_block(
            f"{header}\n\nFix these documentation failures before returning to the user:\n\n{body}"
        )
    else:
        hook_output(f"{header}\n\n{body}")
    return 0


def main() -> int:
    if hooks_disabled():
        return 0
    payload = read_payload()
    if hook_event_name(payload) != "Stop":
        return 0
    return run_repo_docs_stop(payload)


if __name__ == "__main__":
    raise SystemExit(main())
