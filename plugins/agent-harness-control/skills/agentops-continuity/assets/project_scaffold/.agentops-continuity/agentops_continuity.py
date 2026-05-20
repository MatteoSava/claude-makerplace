#!/usr/bin/env python3
"""
AgentOps Continuity: deterministic session ledger, compaction recovery, and stop gates
for Claude Code and Codex.

This script is intentionally dependency-free. It is safe to run from hooks in repos
that do not have Python packages installed yet.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

APP_DIR = ".agentops-continuity"
POLICY_FILE = "policy.json"

DEFAULT_POLICY: dict[str, Any] = {
    "schema_version": "1.0",
    "context_injection": {
        "enabled": True,
        "on_session_start": True,
        "on_user_prompt": True,
        "on_post_tool_batch": True,
        "max_chars": 7000,
        "ledger_tail_lines": 40,
        "decision_tail_lines": 18,
        "risk_tail_lines": 18,
        "next_tail_lines": 18,
    },
    "prompt_tracking": {
        "auto_create_task_on_prompt": True,
        "verification_required_keywords": [
            "implement",
            "create",
            "build",
            "fix",
            "repair",
            "refactor",
            "change",
            "modify",
            "edit",
            "add",
            "delete",
            "remove",
            "migrate",
            "update",
            "test",
        ],
        "ignore_prompt_regexes": [
            r"^/help\b",
            r"^/status\b",
            r"^/hooks\b",
            r"^/skills\b",
        ],
    },
    "compaction": {
        "snapshot_before_compact": True,
        "block_manual_compact_if_missing_current_task": False,
        "update_ledger_after_compact": True,
        "max_summary_chars": 12000,
        "max_snapshots": 24,
    },
    "stop_gate": {
        "enabled": True,
        "allow_when_stop_hook_active": True,
        "block_when_verification_required": True,
        "block_when_pending_next_actions": False,
        "required_verification_statuses": [
            "passed",
            "not-applicable",
            "skipped-with-reason",
            "manual-review",
        ],
        "max_block_count_per_task": 6,
        "override_file": "state/allow-stop.once",
    },
    "tracking": {
        "exclude_path_patterns": [
            ".git/**",
            APP_DIR + "/**",
            ".claude/**",
            ".codex/**",
            ".agents/**",
            "node_modules/**",
            ".venv/**",
            "venv/**",
            "dist/**",
            "build/**",
            "coverage/**",
            ".pytest_cache/**",
            ".mypy_cache/**",
            ".ruff_cache/**",
        ],
        "verification_required_path_patterns": [
            "*.py",
            "*.pyi",
            "*.js",
            "*.jsx",
            "*.ts",
            "*.tsx",
            "*.go",
            "*.rs",
            "*.java",
            "*.kt",
            "*.scala",
            "*.cs",
            "*.rb",
            "*.php",
            "*.swift",
            "*.c",
            "*.cpp",
            "*.h",
            "*.hpp",
            "*.tf",
            "*.tfvars",
            "*.yaml",
            "*.yml",
            "*.toml",
            "*.json",
            "*.sql",
            "Dockerfile",
            "docker-compose*.yml",
            "package.json",
            "pyproject.toml",
            "requirements*.txt",
            "poetry.lock",
            "uv.lock",
            "Pipfile",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle*",
        ],
    },
    "verification_detection": {
        "command_regexes": [
            r"\bpytest\b",
            r"\bpython\s+-m\s+pytest\b",
            r"\bnpm\s+(run\s+)?test\b",
            r"\bpnpm\s+(run\s+)?test\b",
            r"\byarn\s+test\b",
            r"\bvitest\b",
            r"\bjest\b",
            r"\bgo\s+test\b",
            r"\bcargo\s+test\b",
            r"\bmvn\s+test\b",
            r"\bgradle\s+test\b",
            r"\bmake\s+test\b",
            r"\btox\b",
            r"\bnox\b",
            r"\bruff\s+check\b",
            r"\bmypy\b",
            r"\beslint\b",
            r"\btsc\b",
            r"\bterraform\s+plan\b",
            r"\bterraform\s+validate\b",
            r"\btofu\s+plan\b",
            r"\bkubectl\s+diff\b",
            r"\bhelm\s+lint\b",
        ],
        "ignore_success_if_command_contains": [
            "|| true",
            "; true",
            "--help",
            "--version",
        ],
    },
    "pretool_guard": {
        "enabled": True,
        "deny_commands_regexes": [
            r"\brm\s+-rf\s+\.agentops-continuity\b",
            r"\brm\s+-rf\s+\.claude\b.*agentops",
            r"\brm\s+-rf\s+\.codex\b.*agentops",
            r"\bmv\s+\.agentops-continuity\b",
            r"\bchmod\s+-R\s+777\s+\.agentops-continuity\b",
        ],
        "deny_reason": "AgentOps Continuity state/hook files should not be removed by an agentic tool call. Edit policy.json or uninstall intentionally outside the agent loop.",
    },
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:8]


def run_git_root(cwd: Path) -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        p = Path(out.decode().strip()).resolve()
        if p.exists():
            return p
    except Exception:
        return None
    return None


def find_repo_root(cwd: str | Path | None = None) -> Path:
    env_root = os.environ.get("AGENTOPS_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve()
        if p.exists():
            return p

    script_root = Path(__file__).resolve().parent.parent
    if (script_root / APP_DIR).exists():
        return script_root

    start = Path(cwd or os.getcwd()).expanduser().resolve()
    for p in [start, *start.parents]:
        if (p / APP_DIR / POLICY_FILE).exists() or (
            p / APP_DIR / "agentops_continuity.py"
        ).exists():
            return p
    git_root = run_git_root(start)
    if git_root is not None:
        return git_root
    return start


def app_path(root: Path, *parts: str) -> Path:
    return root / APP_DIR / Path(*parts)


def state_path(root: Path, *parts: str) -> Path:
    return app_path(root, "state", *parts)


def ensure_dirs(root: Path) -> None:
    for sub in ["state", "state/snapshots", "reports", "artifacts"]:
        app_path(root, sub).mkdir(parents=True, exist_ok=True)
    for name, default in {
        "session-ledger.md": "# AgentOps session ledger\n\n",
        "context-essentials.md": "# Context essentials\n\nNo curated essentials yet. Use `python .agentops-continuity/agentops_continuity.py context --set ...` or let hooks accumulate state.\n",
        "decisions.md": "# Decisions\n\n",
        "open-risks.md": "# Open risks\n\n",
        "next-actions.md": "# Next actions\n\n",
    }.items():
        p = state_path(root, name)
        if not p.exists():
            p.write_text(default, encoding="utf-8")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_policy(root: Path) -> dict[str, Any]:
    ensure_dirs(root)
    p = app_path(root, POLICY_FILE)
    if not p.exists():
        p.write_text(json.dumps(DEFAULT_POLICY, indent=2), encoding="utf-8")
        return DEFAULT_POLICY
    try:
        user_policy = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(user_policy, dict):
            return DEFAULT_POLICY
        return deep_merge(DEFAULT_POLICY, user_policy)
    except Exception:
        return DEFAULT_POLICY


def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def append_md(path: Path, heading: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {heading}\n\n{body.strip()}\n")


def tail_text(path: Path, lines: int) -> str:
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(data[-lines:]).strip()


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return (
        text[: max_chars - 120].rstrip()
        + "\n\n... [truncated by AgentOps Continuity] ..."
    )


def relpath(root: Path, p: str | Path) -> str:
    try:
        pp = Path(p).expanduser()
        if pp.is_absolute():
            return pp.resolve().relative_to(root.resolve()).as_posix()
        return pp.as_posix().lstrip("./")
    except Exception:
        return str(p).replace("\\", "/").lstrip("./")


def is_excluded(path: str, policy: dict[str, Any]) -> bool:
    path = path.replace("\\", "/").lstrip("./")
    for pat in policy["tracking"].get("exclude_path_patterns", []):
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch("./" + path, pat):
            return True
    return False


def requires_verification(path: str, policy: dict[str, Any]) -> bool:
    path = path.replace("\\", "/").lstrip("./")
    if is_excluded(path, policy):
        return False
    base = Path(path).name
    for pat in policy["tracking"].get("verification_required_path_patterns", []):
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(base, pat):
            return True
    return False


def current_task(root: Path) -> dict[str, Any]:
    return read_json(state_path(root, "current-task.json"), {})


def save_current_task(root: Path, task: dict[str, Any]) -> None:
    if task:
        task["updated_at"] = utcnow()
    write_json(state_path(root, "current-task.json"), task)


def verification_state(root: Path) -> dict[str, Any]:
    return read_json(
        state_path(root, "verification-status.json"),
        {"status": "unknown", "updated_at": None},
    )


def save_verification(
    root: Path, status: str, command: str = "", note: str = "", source: str = "manual"
) -> dict[str, Any]:
    data = {
        "status": status,
        "command": command,
        "note": note,
        "source": source,
        "updated_at": utcnow(),
    }
    write_json(state_path(root, "verification-status.json"), data)
    task = current_task(root)
    if task:
        task["verification"] = data
        if status in {
            "passed",
            "not-applicable",
            "skipped-with-reason",
            "manual-review",
        }:
            task["status"] = "verified"
        elif status == "failed":
            task["status"] = "active"
        save_current_task(root, task)
    append_md(
        state_path(root, "session-ledger.md"),
        f"Verification {status} - {utcnow()}",
        f"command: `{command or 'n/a'}`\n\nsource: {source}\n\n{note}".strip(),
    )
    return data


def task_needs_new(prompt: str, task: dict[str, Any]) -> bool:
    if not task:
        return True
    status = str(task.get("status", "")).lower()
    return status in {"done", "completed", "closed", "abandoned", "verified"}


def prompt_requires_verification(prompt: str, policy: dict[str, Any]) -> bool:
    low = prompt.lower()
    for rx in policy["prompt_tracking"].get("ignore_prompt_regexes", []):
        if re.search(rx, prompt, re.I):
            return False
    return any(
        k.lower() in low
        for k in policy["prompt_tracking"].get("verification_required_keywords", [])
    )


def maybe_create_or_update_task(
    root: Path, prompt: str, policy: dict[str, Any]
) -> None:
    if not policy["prompt_tracking"].get("auto_create_task_on_prompt", True):
        return
    prompt = (prompt or "").strip()
    if not prompt:
        return
    for rx in policy["prompt_tracking"].get("ignore_prompt_regexes", []):
        if re.search(rx, prompt, re.I):
            return
    task = current_task(root)
    if task_needs_new(prompt, task):
        task_id = "task-" + sha8(prompt + utcnow())
        task = {
            "id": task_id,
            "objective": truncate(prompt, 600),
            "status": "active",
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "verification_required": prompt_requires_verification(prompt, policy),
            "verification": verification_state(root),
            "touched_files": [],
            "constraints": [],
            "next_actions": [],
            "stop_block_count": 0,
            "last_prompt_hash": sha8(prompt),
        }
        save_current_task(root, task)
        append_md(
            state_path(root, "session-ledger.md"),
            f"New task {task_id} - {utcnow()}",
            truncate(prompt, 1000),
        )
    else:
        task["last_prompt_hash"] = sha8(prompt)
        task.setdefault("prompt_history", [])
        task["prompt_history"] = (
            task["prompt_history"]
            + [{"at": utcnow(), "hash": sha8(prompt), "preview": truncate(prompt, 200)}]
        )[-10:]
        if prompt_requires_verification(prompt, policy):
            task["verification_required"] = True
        save_current_task(root, task)
        append_md(
            state_path(root, "session-ledger.md"),
            f"Prompt - {utcnow()}",
            truncate(prompt, 1000),
        )


def extract_paths_from_command(command: str) -> set[str]:
    paths: set[str] = set()
    patterns = [
        r"\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(.+)",
        r"^\+\+\+\s+b/(.+)$",
        r"^---\s+a/(.+)$",
        r"^diff\s+--git\s+a/(.+?)\s+b/(.+)$",
    ]
    for line in command.splitlines():
        for pat in patterns:
            m = re.search(pat, line.strip())
            if m:
                for g in m.groups():
                    if g and g != "/dev/null":
                        paths.add(g.strip().strip("\"'"))
    return paths


def extract_tool_paths(payload: dict[str, Any], root: Path) -> set[str]:
    tool_name = str(payload.get("tool_name", ""))
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return set()
    paths: set[str] = set()
    for key in [
        "file_path",
        "filePath",
        "path",
        "notebook_path",
        "target_file",
        "filename",
    ]:
        val = ti.get(key)
        if isinstance(val, str) and val.strip():
            paths.add(relpath(root, val))
    command = ti.get("command")
    if isinstance(command, str):
        if (
            tool_name in {"apply_patch", "Bash"}
            or "apply_patch" in command
            or "*** Begin Patch" in command
        ):
            paths |= {relpath(root, p) for p in extract_paths_from_command(command)}
    return {p for p in paths if p and not p.startswith("-")}


def mark_touched(
    root: Path, paths: Iterable[str], source: str, policy: dict[str, Any]
) -> list[str]:
    normalized: list[str] = []
    for p in paths:
        rp = relpath(root, p)
        if not rp or is_excluded(rp, policy):
            continue
        normalized.append(rp)
    if not normalized:
        return []

    touched = read_json(state_path(root, "touched-files.json"), {})
    if not isinstance(touched, dict):
        touched = {}
    now = utcnow()
    for rp in normalized:
        entry = touched.get(rp) or {"first_seen": now, "events": []}
        entry["last_seen"] = now
        entry["events"] = (entry.get("events", []) + [{"at": now, "source": source}])[
            -12:
        ]
        touched[rp] = entry
    write_json(state_path(root, "touched-files.json"), touched)

    task = current_task(root)
    if task:
        existing = set(task.get("touched_files") or [])
        task["touched_files"] = sorted(existing | set(normalized))
        if any(requires_verification(p, policy) for p in normalized):
            task["verification_required"] = True
            v = task.get("verification") or {}
            if v.get("status") in {
                "passed",
                "not-applicable",
                "skipped-with-reason",
                "manual-review",
            }:
                task["verification"] = {
                    "status": "unknown",
                    "note": "Changed files after previous verification",
                    "updated_at": now,
                }
                write_json(
                    state_path(root, "verification-status.json"), task["verification"]
                )
        save_current_task(root, task)
    append_md(
        state_path(root, "session-ledger.md"),
        f"Touched files - {now}",
        "\n".join(f"- `{p}` ({source})" for p in normalized),
    )
    return normalized


def command_is_verification(command: str, policy: dict[str, Any]) -> bool:
    for bad in policy["verification_detection"].get(
        "ignore_success_if_command_contains", []
    ):
        if bad in command:
            return False
    return any(
        re.search(rx, command, re.I)
        for rx in policy["verification_detection"].get("command_regexes", [])
    )


def deny_guarded_command(command: str, policy: dict[str, Any]) -> str | None:
    guard = policy.get("pretool_guard", {})
    if not guard.get("enabled", True):
        return None
    for rx in guard.get("deny_commands_regexes", []):
        if re.search(rx, command, re.I | re.S):
            return (
                guard.get("deny_reason")
                or "Blocked by AgentOps Continuity pretool guard."
            )
    return None


def latest_compact_summary(root: Path) -> str:
    p = state_path(root, "latest-compact-summary.md")
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def build_context(root: Path, policy: dict[str, Any], reason: str = "") -> str:
    ci = policy.get("context_injection", {})
    max_chars = int(ci.get("max_chars", 7000))
    ledger_tail = tail_text(
        state_path(root, "session-ledger.md"), int(ci.get("ledger_tail_lines", 40))
    )
    decision_tail = tail_text(
        state_path(root, "decisions.md"), int(ci.get("decision_tail_lines", 18))
    )
    risks_tail = tail_text(
        state_path(root, "open-risks.md"), int(ci.get("risk_tail_lines", 18))
    )
    next_tail = tail_text(
        state_path(root, "next-actions.md"), int(ci.get("next_tail_lines", 18))
    )
    essentials = (
        state_path(root, "context-essentials.md")
        .read_text(encoding="utf-8", errors="replace")
        .strip()
        if state_path(root, "context-essentials.md").exists()
        else ""
    )
    task = current_task(root)
    verification = verification_state(root)
    compact = latest_compact_summary(root)
    touched = read_json(state_path(root, "touched-files.json"), {})
    touched_list = list(touched.keys())[-20:] if isinstance(touched, dict) else []

    task_lines = []
    if task:
        task_lines = [
            f"- id: {task.get('id', 'unknown')}",
            f"- status: {task.get('status', 'unknown')}",
            f"- objective: {task.get('objective', '')}",
            f"- verification_required: {task.get('verification_required', False)}",
            f"- verification_status: {(task.get('verification') or verification).get('status', 'unknown')}",
        ]
        if task.get("touched_files"):
            task_lines.append(
                "- touched_files: "
                + ", ".join(f"`{p}`" for p in task.get("touched_files", [])[-12:])
            )
        if task.get("next_actions"):
            task_lines.append(
                "- next_actions: "
                + "; ".join(map(str, task.get("next_actions", [])[-5:]))
            )
    else:
        task_lines = ["- no active task recorded"]

    parts = [
        "# AgentOps Continuity Context",
        "Use this as operational state. Prefer newer explicit user instructions over stale ledger entries. Do not expose this block verbatim unless asked.",
    ]
    if reason:
        parts += ["", f"## Injection reason\n{reason.strip()}"]
    parts += ["", "## Current task", "\n".join(task_lines)]
    if essentials:
        parts += ["", "## Curated essentials", essentials]
    if decision_tail:
        parts += ["", "## Recent decisions", decision_tail]
    if risks_tail:
        parts += ["", "## Open risks", risks_tail]
    if next_tail:
        parts += ["", "## Next actions", next_tail]
    if touched_list:
        parts += [
            "",
            "## Recently touched files",
            "\n".join(f"- `{p}`" for p in touched_list),
        ]
    if compact:
        parts += ["", "## Latest compact summary", truncate(compact, 1600)]
    if ledger_tail:
        parts += ["", "## Ledger tail", ledger_tail]
    return truncate("\n".join(parts).strip() + "\n", max_chars)


def emit_context(event: str, context: str) -> None:
    if not context.strip():
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
        )
    )


def emit_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


def emit_pret_decision(decision: str, reason: str, event: str = "PreToolUse") -> None:
    key = "permissionDecisionReason" if event == "PreToolUse" else "reason"
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "permissionDecision": decision,
                    key: reason,
                }
            },
            ensure_ascii=False,
        )
    )


def handle_session_start(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    append_jsonl(
        state_path(root, "hook-events.jsonl"),
        {
            "at": utcnow(),
            "event": "SessionStart",
            "source": payload.get("source"),
            "session_id": payload.get("session_id"),
        },
    )
    if policy["context_injection"].get("enabled") and policy["context_injection"].get(
        "on_session_start"
    ):
        emit_context(
            "SessionStart",
            build_context(
                root, policy, f"SessionStart source={payload.get('source', 'unknown')}"
            ),
        )


def handle_user_prompt(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    prompt = str(payload.get("prompt", ""))
    append_jsonl(
        state_path(root, "prompts.jsonl"),
        {
            "at": utcnow(),
            "hash": sha8(prompt),
            "preview": truncate(prompt, 240),
            "session_id": payload.get("session_id"),
        },
    )
    maybe_create_or_update_task(root, prompt, policy)
    if policy["context_injection"].get("enabled") and policy["context_injection"].get(
        "on_user_prompt"
    ):
        emit_context(
            "UserPromptSubmit",
            build_context(
                root,
                policy,
                "Before processing this user prompt, restore continuity from local state.",
            ),
        )


def handle_pretool(root: Path, payload: dict[str, Any], policy: dict[str, Any]) -> None:
    ti = payload.get("tool_input") or {}
    command = ti.get("command") if isinstance(ti, dict) else None
    if isinstance(command, str):
        reason = deny_guarded_command(command, policy)
        if reason:
            append_jsonl(
                state_path(root, "blocked-tools.jsonl"),
                {
                    "at": utcnow(),
                    "event": "PreToolUse",
                    "tool": payload.get("tool_name"),
                    "command_hash": sha8(command),
                    "reason": reason,
                },
            )
            emit_pret_decision("deny", reason)
            return
    paths = extract_tool_paths(payload, root)
    if paths:
        mark_touched(
            root,
            paths,
            "PreToolUse:" + str(payload.get("tool_name", "unknown")),
            policy,
        )


def handle_posttool(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    tool = str(payload.get("tool_name", ""))
    paths = extract_tool_paths(payload, root)
    if paths:
        touched = mark_touched(root, paths, "PostToolUse:" + tool, policy)
        if touched:
            emit_context(
                "PostToolUse",
                f"AgentOps noticed changed files: {', '.join(touched[-8:])}. Update the task ledger and run/record verification before final response if these affect code/config.",
            )
            return
    ti = payload.get("tool_input") or {}
    command = ti.get("command") if isinstance(ti, dict) else None
    if isinstance(command, str) and command_is_verification(command, policy):
        save_verification(root, "passed", command=command, source="PostToolUse")
        emit_context(
            "PostToolUse",
            f"AgentOps recorded verification as passed from command: `{command}`.",
        )


def handle_posttool_failure(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    ti = payload.get("tool_input") or {}
    command = ti.get("command") if isinstance(ti, dict) else None
    if isinstance(command, str) and command_is_verification(command, policy):
        save_verification(
            root,
            "failed",
            command=command,
            note=str(payload.get("error", "tool failed")),
            source="PostToolUseFailure",
        )
        emit_context(
            "PostToolUseFailure",
            f"AgentOps recorded verification as failed from command: `{command}`. Fix or explicitly mark not applicable before final response.",
        )


def handle_posttool_batch(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    append_jsonl(
        state_path(root, "tool-batches.jsonl"),
        {
            "at": utcnow(),
            "count": len(payload.get("tool_calls") or []),
            "session_id": payload.get("session_id"),
        },
    )
    if policy["context_injection"].get("enabled") and policy["context_injection"].get(
        "on_post_tool_batch"
    ):
        task = current_task(root)
        if (
            task
            and task.get("verification_required")
            and (task.get("verification") or {}).get("status")
            not in policy["stop_gate"].get("required_verification_statuses", [])
        ):
            emit_context(
                "PostToolBatch",
                "AgentOps reminder: touched files or the active task require verification before final response. Run an appropriate test/check or mark verification not-applicable with a reason.",
            )


def handle_precompact(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    trigger = payload.get("trigger", "unknown")
    append_jsonl(
        state_path(root, "hook-events.jsonl"),
        {
            "at": utcnow(),
            "event": "PreCompact",
            "trigger": trigger,
            "session_id": payload.get("session_id"),
        },
    )
    if policy["compaction"].get("snapshot_before_compact", True):
        snapshot = snapshot_state(
            root,
            policy,
            label=f"precompact-{trigger}",
            extra={
                "payload": {
                    k: payload.get(k)
                    for k in [
                        "session_id",
                        "trigger",
                        "custom_instructions",
                        "transcript_path",
                    ]
                }
            },
        )
        append_md(
            state_path(root, "session-ledger.md"),
            f"PreCompact snapshot - {utcnow()}",
            f"trigger: {trigger}\n\nsnapshot: `{snapshot.relative_to(root).as_posix()}`",
        )
    if (
        trigger == "manual"
        and policy["compaction"].get(
            "block_manual_compact_if_missing_current_task", False
        )
        and not current_task(root)
    ):
        emit_block(
            "AgentOps Continuity has no current-task snapshot. Create or confirm current task before manual compaction."
        )


def handle_postcompact(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    summary = str(payload.get("compact_summary", ""))
    trigger = payload.get("trigger", "unknown")
    max_chars = int(policy["compaction"].get("max_summary_chars", 12000))
    summary = truncate(summary, max_chars)
    append_jsonl(
        state_path(root, "compact-summaries.jsonl"),
        {
            "at": utcnow(),
            "trigger": trigger,
            "summary": summary,
            "session_id": payload.get("session_id"),
        },
    )
    state_path(root, "latest-compact-summary.md").write_text(
        f"# Latest compact summary\n\ntrigger: {trigger}\nat: {utcnow()}\n\n{summary}\n",
        encoding="utf-8",
    )
    if policy["compaction"].get("update_ledger_after_compact", True):
        append_md(
            state_path(root, "session-ledger.md"),
            f"PostCompact - {utcnow()}",
            f"trigger: {trigger}\n\nsummary_hash: `{sha8(summary)}`\n\n{truncate(summary, 1200)}",
        )


def consume_stop_override(root: Path, policy: dict[str, Any]) -> str | None:
    override_rel = policy["stop_gate"].get("override_file", "state/allow-stop.once")
    p = (
        app_path(root, override_rel)
        if not override_rel.startswith("/")
        else Path(override_rel)
    )
    if p.exists():
        reason = (
            p.read_text(encoding="utf-8", errors="replace").strip()
            or "one-shot override"
        )
        try:
            p.unlink()
        except Exception:
            pass
        append_md(
            state_path(root, "session-ledger.md"),
            f"Stop override consumed - {utcnow()}",
            reason,
        )
        return reason
    return None


def handle_stop(root: Path, payload: dict[str, Any], policy: dict[str, Any]) -> None:
    gate = policy.get("stop_gate", {})
    append_jsonl(
        state_path(root, "hook-events.jsonl"),
        {
            "at": utcnow(),
            "event": "Stop",
            "session_id": payload.get("session_id"),
            "stop_hook_active": payload.get("stop_hook_active"),
        },
    )
    if not gate.get("enabled", True):
        return
    if payload.get("stop_hook_active") and gate.get(
        "allow_when_stop_hook_active", True
    ):
        return
    override = consume_stop_override(root, policy)
    if override:
        return
    task = current_task(root)
    if not task:
        return
    accepted = set(gate.get("required_verification_statuses", []))
    verification = task.get("verification") or verification_state(root)
    vstatus = str(verification.get("status", "unknown"))
    status = str(task.get("status", "active")).lower()
    if status in {"done", "closed", "completed", "abandoned"}:
        return
    if (
        gate.get("block_when_verification_required", True)
        and task.get("verification_required")
        and vstatus not in accepted
    ):
        count = int(task.get("stop_block_count", 0)) + 1
        task["stop_block_count"] = count
        save_current_task(root, task)
        if count > int(gate.get("max_block_count_per_task", 6)):
            append_md(
                state_path(root, "session-ledger.md"),
                f"Stop gate max block count reached - {utcnow()}",
                f"task: {task.get('id')} verification_status: {vstatus}",
            )
            return
        touched = task.get("touched_files") or []
        reason = textwrap.dedent(f"""
        AgentOps Continuity gate: active task `{task.get("id", "unknown")}` requires verification before final response.

        Objective: {task.get("objective", "")}
        Verification status: {vstatus}
        Touched files: {", ".join(touched[-12:]) if touched else "none recorded"}

        Continue by running a relevant test/check. If verification genuinely does not apply, run:
        python .agentops-continuity/agentops_continuity.py mark-verified --kind not-applicable --note "why verification is not applicable"

        Then provide the final answer with the verification evidence.
        """).strip()
        append_md(
            state_path(root, "session-ledger.md"), f"Stop blocked - {utcnow()}", reason
        )
        emit_block(reason)
        return
    if gate.get("block_when_pending_next_actions", False) and task.get("next_actions"):
        reason = "AgentOps Continuity gate: pending next_actions exist. Complete them or clear them before final response."
        append_md(
            state_path(root, "session-ledger.md"), f"Stop blocked - {utcnow()}", reason
        )
        emit_block(reason)


def handle_session_end(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    append_jsonl(
        state_path(root, "hook-events.jsonl"),
        {
            "at": utcnow(),
            "event": "SessionEnd",
            "reason": payload.get("reason"),
            "session_id": payload.get("session_id"),
        },
    )
    snapshot_state(
        root, policy, label="session-end", extra={"reason": payload.get("reason")}
    )


def handle_config_change(
    root: Path, payload: dict[str, Any], policy: dict[str, Any]
) -> None:
    append_jsonl(
        state_path(root, "config-changes.jsonl"), {"at": utcnow(), "payload": payload}
    )


def snapshot_state(
    root: Path,
    policy: dict[str, Any],
    label: str = "snapshot",
    extra: dict[str, Any] | None = None,
) -> Path:
    ensure_dirs(root)
    name = f"{slug_time()}-{label}.md".replace("/", "-")
    p = state_path(root, "snapshots", name)
    sections = [
        f"# AgentOps snapshot: {label}",
        f"at: {utcnow()}",
        "",
        "## Context",
        build_context(root, policy, f"snapshot:{label}"),
    ]
    if extra:
        sections += [
            "",
            "## Extra",
            "```json",
            json.dumps(extra, indent=2, ensure_ascii=False),
            "```",
        ]
    p.write_text("\n".join(sections), encoding="utf-8")
    cleanup_snapshots(root, policy)
    return p


def cleanup_snapshots(root: Path, policy: dict[str, Any]) -> None:
    max_snapshots = int(policy.get("compaction", {}).get("max_snapshots", 24))
    sdir = state_path(root, "snapshots")
    snaps = sorted(sdir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in snaps[max_snapshots:]:
        try:
            old.unlink()
        except Exception:
            pass


def handle_hook(payload: dict[str, Any]) -> int:
    root = find_repo_root(payload.get("cwd"))
    policy = load_policy(root)
    event = str(payload.get("hook_event_name", ""))
    try:
        if event == "SessionStart":
            handle_session_start(root, payload, policy)
        elif event == "UserPromptSubmit":
            handle_user_prompt(root, payload, policy)
        elif event == "PreToolUse":
            handle_pretool(root, payload, policy)
        elif event == "PostToolUse":
            handle_posttool(root, payload, policy)
        elif event == "PostToolUseFailure":
            handle_posttool_failure(root, payload, policy)
        elif event == "PostToolBatch":
            handle_posttool_batch(root, payload, policy)
        elif event == "Stop":
            handle_stop(root, payload, policy)
        elif event == "PreCompact":
            handle_precompact(root, payload, policy)
        elif event == "PostCompact":
            handle_postcompact(root, payload, policy)
        elif event == "SessionEnd":
            handle_session_end(root, payload, policy)
        elif event == "ConfigChange":
            handle_config_change(root, payload, policy)
        else:
            append_jsonl(
                state_path(root, "hook-events.jsonl"),
                {
                    "at": utcnow(),
                    "event": event or "unknown",
                    "session_id": payload.get("session_id"),
                },
            )
    except Exception as exc:
        # Hooks should fail open by default unless a specific decision has been emitted.
        append_jsonl(
            state_path(root, "errors.jsonl"),
            {"at": utcnow(), "event": event, "error": repr(exc)},
        )
        print(f"AgentOps Continuity hook error: {exc}", file=sys.stderr)
        return 1
    return 0


def read_stdin_json() -> dict[str, Any]:
    data = sys.stdin.read()
    if not data.strip():
        return {}
    try:
        obj = json.loads(data)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON: {exc}", file=sys.stderr)
        return {}


def cmd_status(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    task = current_task(root)
    verification = verification_state(root)
    touched = read_json(state_path(root, "touched-files.json"), {})
    print("AgentOps Continuity status")
    print(f"root: {root}")
    print(f"state: {state_path(root)}")
    print(f"policy: {app_path(root, POLICY_FILE)}")
    print(f"task: {task.get('id', 'none') if task else 'none'}")
    if task:
        print(f"objective: {task.get('objective', '')}")
        print(f"status: {task.get('status', 'unknown')}")
        print(f"verification_required: {task.get('verification_required', False)}")
    print(
        f"verification: {verification.get('status', 'unknown')} {verification.get('command', '')}"
    )
    print(f"touched_files: {len(touched) if isinstance(touched, dict) else 0}")
    return 0


def cmd_new_task(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    load_policy(root)
    objective = args.objective or " ".join(args.words).strip()
    if not objective:
        print("Provide an objective", file=sys.stderr)
        return 2
    task: dict[str, Any] = {
        "id": args.id or "task-" + sha8(objective + utcnow()),
        "objective": objective,
        "status": "active",
        "created_at": utcnow(),
        "updated_at": utcnow(),
        "verification_required": bool(args.verification_required),
        "verification": {"status": "unknown", "updated_at": utcnow()},
        "touched_files": [],
        "constraints": [],
        "next_actions": [],
        "stop_block_count": 0,
    }
    save_current_task(root, task)
    write_json(state_path(root, "verification-status.json"), task["verification"])
    append_md(
        state_path(root, "session-ledger.md"),
        f"New task {task['id']} - {utcnow()}",
        objective,
    )
    print(json.dumps(task, indent=2, ensure_ascii=False))
    return 0


def cmd_mark_verified(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    load_policy(root)
    save_verification(
        root, args.kind, command=args.command or "", note=args.note or "", source="cli"
    )
    print(f"AgentOps verification recorded: {args.kind}")
    return 0


def cmd_decision(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    load_policy(root)
    text = args.text or " ".join(args.words).strip()
    append_md(state_path(root, "decisions.md"), f"Decision - {utcnow()}", text)
    append_md(state_path(root, "session-ledger.md"), f"Decision - {utcnow()}", text)
    print("Decision recorded")
    return 0


def cmd_risk(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    load_policy(root)
    text = args.text or " ".join(args.words).strip()
    append_md(state_path(root, "open-risks.md"), f"Risk - {utcnow()}", text)
    append_md(state_path(root, "session-ledger.md"), f"Risk - {utcnow()}", text)
    print("Risk recorded")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    load_policy(root)
    text = args.text or " ".join(args.words).strip()
    append_md(state_path(root, "next-actions.md"), f"Next action - {utcnow()}", text)
    task = current_task(root)
    if task:
        task.setdefault("next_actions", [])
        task["next_actions"] = (task["next_actions"] + [text])[-12:]
        save_current_task(root, task)
    print("Next action recorded")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    policy = load_policy(root)
    p = state_path(root, "context-essentials.md")
    if args.set:
        p.write_text(args.set.strip() + "\n", encoding="utf-8")
        print("Context essentials replaced")
    elif args.append:
        append_md(p, f"Update - {utcnow()}", args.append)
        print("Context essentials appended")
    else:
        print(build_context(root, policy, "manual context render"))
    return 0


def cmd_touch(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    policy = load_policy(root)
    touched = mark_touched(root, args.paths, "cli", policy)
    print("Touched: " + ", ".join(touched))
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    policy = load_policy(root)
    p = snapshot_state(root, policy, args.label)
    print(p)
    return 0


def cmd_allow_stop(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    policy = load_policy(root)
    override_rel = policy["stop_gate"].get("override_file", "state/allow-stop.once")
    p = (
        app_path(root, override_rel)
        if not override_rel.startswith("/")
        else Path(override_rel)
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args.reason or "Manual one-shot stop gate override", encoding="utf-8")
    print(f"One-shot stop override written: {p}")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    target = state_path(root)
    if args.hard and target.exists():
        shutil.rmtree(target)
    ensure_dirs(root)
    if not args.keep_task:
        for name in [
            "current-task.json",
            "verification-status.json",
            "touched-files.json",
        ]:
            p = state_path(root, name)
            if p.exists():
                p.unlink()
    print("AgentOps state reset")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = find_repo_root(args.cwd)
    policy = load_policy(root)
    errors = []
    if not app_path(root, "agentops_continuity.py").exists():
        errors.append("missing .agentops-continuity/agentops_continuity.py")
    if not app_path(root, POLICY_FILE).exists():
        errors.append("missing policy.json")
    if not isinstance(policy.get("schema_version"), str):
        errors.append("policy schema_version should be a string")
    ensure_dirs(root)
    if errors:
        print("AgentOps doctor found issues:")
        for e in errors:
            print(f"- {e}")
        return 1
    print("AgentOps doctor OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AgentOps Continuity hook core")
    p.add_argument("--cwd", default=None, help="Repo working directory override")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hook", help="Read hook JSON from stdin and dispatch")
    sub.add_parser("status", help="Print state summary")
    sp = sub.add_parser("new-task", help="Create/replace current task")
    sp.add_argument("words", nargs="*", help="Objective words")
    sp.add_argument("--objective", default="")
    sp.add_argument("--id", default="")
    sp.add_argument("--verification-required", action="store_true")
    sp = sub.add_parser("mark-verified", help="Record verification status")
    sp.add_argument(
        "--kind",
        required=True,
        choices=[
            "passed",
            "failed",
            "not-applicable",
            "skipped-with-reason",
            "manual-review",
        ],
    )
    sp.add_argument("--command", default="")
    sp.add_argument("--note", default="")
    sp = sub.add_parser("decision", help="Append an architectural/operational decision")
    sp.add_argument("words", nargs="*")
    sp.add_argument("--text", default="")
    sp = sub.add_parser("risk", help="Append an open risk")
    sp.add_argument("words", nargs="*")
    sp.add_argument("--text", default="")
    sp = sub.add_parser("next", help="Append a next action")
    sp.add_argument("words", nargs="*")
    sp.add_argument("--text", default="")
    sp = sub.add_parser("context", help="Render or edit context essentials")
    sp.add_argument("--set", default="")
    sp.add_argument("--append", default="")
    sp = sub.add_parser("touch", help="Mark touched files")
    sp.add_argument("paths", nargs="+")
    sp = sub.add_parser("snapshot", help="Write a state snapshot")
    sp.add_argument("--label", default="manual")
    sp = sub.add_parser("allow-stop", help="Create a one-shot stop gate override")
    sp.add_argument("--reason", default="")
    sp = sub.add_parser("reset", help="Reset local state")
    sp.add_argument("--hard", action="store_true")
    sp.add_argument("--keep-task", action="store_true")
    sub.add_parser("doctor", help="Validate installation")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "hook":
        return handle_hook(read_stdin_json())
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "new-task":
        return cmd_new_task(args)
    if args.cmd == "mark-verified":
        return cmd_mark_verified(args)
    if args.cmd == "decision":
        return cmd_decision(args)
    if args.cmd == "risk":
        return cmd_risk(args)
    if args.cmd == "next":
        return cmd_next(args)
    if args.cmd == "context":
        return cmd_context(args)
    if args.cmd == "touch":
        return cmd_touch(args)
    if args.cmd == "snapshot":
        return cmd_snapshot(args)
    if args.cmd == "allow-stop":
        return cmd_allow_stop(args)
    if args.cmd == "reset":
        return cmd_reset(args)
    if args.cmd == "doctor":
        return cmd_doctor(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
