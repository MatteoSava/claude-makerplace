#!/usr/bin/env python3
"""
Repo Sentinel: deterministic guardrails for AI coding agents.

This script is intentionally dependency-free so it can run from Claude Code and
Codex hooks without a virtualenv. It accepts hook JSON on stdin and emits hook
JSON on stdout using shapes accepted by Claude Code and Codex.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "0.1.0"
DEFAULT_POLICY_PATH = ".repo-sentinel/policy.json"
STATE_DIR = ".repo-sentinel/state"


def _now() -> float:
    return time.time()


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=None, separators=(",", ":"))


def _read_json_stdin() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError as exc:
        print(f"repo-sentinel: invalid hook JSON on stdin: {exc}", file=sys.stderr)
    return {}


def _run(
    cmd: Sequence[str], cwd: Optional[Path] = None, timeout: int = 5
) -> Tuple[int, str, str]:
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return cp.returncode, cp.stdout, cp.stderr
    except Exception as exc:  # pragma: no cover - defensive
        return 127, "", str(exc)


def find_repo_root(cwd: Optional[str] = None) -> Path:
    start = Path(cwd or os.getcwd()).resolve()
    code, out, _ = _run(["git", "rev-parse", "--show-toplevel"], cwd=start, timeout=3)
    if code == 0 and out.strip():
        return Path(out.strip()).resolve()
    return start


def load_policy(repo: Path, explicit: Optional[str] = None) -> Dict[str, Any]:
    path = Path(explicit) if explicit else repo / DEFAULT_POLICY_PATH
    if not path.is_absolute():
        path = repo / path
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default_policy()
    except Exception as exc:
        # Fail closed for hooks if policy is malformed.
        return {
            "__policy_error__": f"Could not read policy {path}: {exc}",
            **default_policy(),
        }


def default_policy() -> Dict[str, Any]:
    return {
        "version": 1,
        "mode": "strict",
        "overrides": {
            "allow_all_env": "REPO_SENTINEL_ALLOW_ALL",
            "allow_destructive_env": "REPO_SENTINEL_ALLOW_DESTRUCTIVE",
            "allow_config_change_env": "REPO_SENTINEL_ALLOW_CONFIG_CHANGE",
            "allow_secret_write_env": "REPO_SENTINEL_ALLOW_SECRET_WRITE",
        },
        "protected_paths": [
            ".git/**",
            "**/.git/**",
            ".repo-sentinel/**",
            ".claude/settings*.json",
            ".claude/hooks/**",
            ".codex/**",
            ".agents/**",
            ".env",
            ".env.*",
            "**/.env",
            "**/.env.*",
            "**/*secret*",
            "**/*credential*",
            "**/*token*",
            "**/*.pem",
            "**/*.key",
            "**/*.p12",
            "**/*.pfx",
            ".ssh/**",
            "**/.ssh/**",
            ".aws/**",
            ".kube/**",
            "node_modules/**",
            "**/node_modules/**",
            ".venv/**",
            "venv/**",
            "**/.venv/**",
            "**/venv/**",
            "dist/**",
            "build/**",
            ".next/**",
            ".turbo/**",
            "coverage/**",
        ],
        "generated_paths": [
            "node_modules/**",
            "dist/**",
            "build/**",
            "coverage/**",
            ".next/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/.pytest_cache/**",
        ],
        "migration_guard": {
            "protect_existing": True,
            "patterns": [
                "**/migrations/*.py",
                "**/migrations/*.sql",
                "**/db/migrate/*",
                "**/schema_migrations/*",
            ],
        },
        "shell": {
            "deny_regex": [
                {
                    "name": "recursive-root-delete",
                    "pattern": r"(?is)(^|[;&|]\s*)rm\s+-(?:[^\s]*[rf][^\s]*|[^\s]*[fr][^\s]*)(?:\s+--)?\s+(?:/|/\*|~|~/|\.\.?)(?:\s|$)",
                    "reason": "Recursive delete against root/home/current directory is blocked.",
                },
                {
                    "name": "git-reset-hard",
                    "pattern": r"(?is)(^|[;&|]\s*)git\s+reset\s+--hard\b",
                    "reason": "git reset --hard destroys uncommitted work.",
                },
                {
                    "name": "git-clean-force",
                    "pattern": r"(?is)(^|[;&|]\s*)git\s+clean\s+-[^\s]*(?:f[^\s]*d|d[^\s]*f|x)[^\s]*\b",
                    "reason": "git clean with force can delete untracked work.",
                },
                {
                    "name": "git-restore-everything",
                    "pattern": r"(?is)(^|[;&|]\s*)git\s+(?:checkout|restore)\s+(?:--\s+)?\.\s*$",
                    "reason": "Bulk git restore/checkout of the whole tree is blocked.",
                },
                {
                    "name": "curl-pipe-shell",
                    "pattern": r"(?is)(curl|wget)\b[^|;]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|fish|python|python3|ruby|perl)\b",
                    "reason": "Piping remote code directly into an interpreter is blocked.",
                },
                {
                    "name": "terraform-apply-destroy",
                    "pattern": r"(?is)(^|[;&|]\s*)(?:terraform|tofu)\s+(?:apply|destroy)\b",
                    "reason": "Infrastructure apply/destroy requires human execution outside the agent loop.",
                },
                {
                    "name": "kubectl-delete",
                    "pattern": r"(?is)(^|[;&|]\s*)kubectl\s+delete\b",
                    "reason": "Kubernetes delete operations are blocked by default.",
                },
                {
                    "name": "helm-destructive",
                    "pattern": r"(?is)(^|[;&|]\s*)helm\s+(?:uninstall|delete|upgrade\b[^;&|]*--force)\b",
                    "reason": "Potentially destructive Helm operations are blocked by default.",
                },
                {
                    "name": "docker-prune",
                    "pattern": r"(?is)(^|[;&|]\s*)docker\s+(?:system|volume|network|image|container)\s+prune\b",
                    "reason": "Docker prune can destroy shared local state.",
                },
                {
                    "name": "docker-compose-down-volume",
                    "pattern": r"(?is)(^|[;&|]\s*)docker\s+compose\s+down\b[^;&|]*\s-v\b",
                    "reason": "docker compose down -v deletes volumes.",
                },
                {
                    "name": "chmod-777",
                    "pattern": r"(?is)(^|[;&|]\s*)chmod\s+-R\s+777\b",
                    "reason": "Recursive chmod 777 is blocked.",
                },
                {
                    "name": "disk-format",
                    "pattern": r"(?is)(^|[;&|]\s*)(?:mkfs|fdisk|parted|diskutil\s+erase|dd\s+[^;&|]*of=/dev/)\b",
                    "reason": "Disk formatting/writing commands are blocked.",
                },
                {
                    "name": "env-file-read",
                    "pattern": r"(?is)(^|[;&|]\s*)(?:cat|less|more|tail|head|grep|rg)\b[^;&|]*(?:^|\s)(?:\.env(?:\.[\w.-]+)?|.*secret.*|.*credential.*)(?:\s|$)",
                    "reason": "Reading local secret files through shell is blocked.",
                },
            ],
            "warn_regex": [
                {
                    "name": "sudo",
                    "pattern": r"(?is)(^|[;&|]\s*)sudo\b",
                    "message": "sudo command detected; keep privilege escalation outside agent automation unless explicitly intended.",
                },
                {
                    "name": "network-upload",
                    "pattern": r"(?is)(?:curl|wget)\b[^;&|]*(?:--data|--data-binary|-d)\s+@",
                    "message": "Command appears to upload a local file over the network.",
                },
                {
                    "name": "broad-rm",
                    "pattern": r"(?is)(^|[;&|]\s*)rm\s+-[^\s]*(?:r|f)[^\s]*\b",
                    "message": "Recursive/force delete detected; verify target is disposable.",
                },
            ],
            "verification_success_regex": [
                r"(?is)(^|[;&|]\s*)(?:python\s+-m\s+pytest|pytest|uv\s+run\s+pytest|tox|nox)\b",
                r"(?is)(^|[;&|]\s*)(?:npm|pnpm|yarn|bun)\s+(?:test|run\s+test|run\s+lint|run\s+typecheck)\b",
                r"(?is)(^|[;&|]\s*)(?:go\s+test|cargo\s+test|mvn\s+test|gradle\s+test|./gradlew\s+test|make\s+(?:test|lint|check))\b",
                r"(?is)(^|[;&|]\s*)(?:ruff\s+check|mypy|pyright|eslint|tsc\b|prettier\s+--check)\b",
                r"(?is)(^|[;&|]\s*)python\s+\.repo-sentinel/repo_sentinel\.py\s+check\b",
            ],
        },
        "secret_scan": {
            "enabled": True,
            "max_file_bytes": 1048576,
            "patterns": [
                {"name": "AWS access key", "regex": r"AKIA[0-9A-Z]{16}"},
                {"name": "GitHub token", "regex": r"gh[pousr]_[A-Za-z0-9_]{36,}"},
                {"name": "OpenAI-style API key", "regex": r"sk-[A-Za-z0-9_-]{32,}"},
                {
                    "name": "Private key header",
                    "regex": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
                },
                {"name": "Slack token", "regex": r"xox[baprs]-[A-Za-z0-9-]{20,}"},
            ],
        },
        "verification": {
            "require_on_stop": True,
            "allow_docs_only_stop": True,
            "max_stop_continuations_per_turn": 1,
            "code_globs": [
                "**/*.py",
                "**/*.js",
                "**/*.jsx",
                "**/*.ts",
                "**/*.tsx",
                "**/*.go",
                "**/*.rs",
                "**/*.java",
                "**/*.kt",
                "**/*.c",
                "**/*.cpp",
                "**/*.h",
                "**/*.hpp",
                "**/*.cs",
                "**/*.rb",
                "**/*.php",
                "**/*.swift",
                "**/*.scala",
                "**/*.sql",
                "Dockerfile",
                "**/Dockerfile",
                "**/*.tf",
                "**/*.yaml",
                "**/*.yml",
            ],
            "docs_globs": ["docs/**", "**/*.md", "**/*.rst", "**/*.txt"],
            "ignore_globs": [
                ".repo-sentinel/**",
                ".git/**",
                ".claude/**",
                ".codex/**",
                ".agents/**",
                "node_modules/**",
                "dist/**",
                "build/**",
                "coverage/**",
            ],
        },
        "prompt_guard": {
            "enabled": True,
            "block_regex": [
                r"(?is)\b(disable|remove|bypass)\b[^\n]{0,80}\b(repo[-_ ]?sentinel|hooks?|guardrails?)\b",
                r"(?is)\bignore\b[^\n]{0,80}\b(repo[-_ ]?sentinel|safety hook|policy)\b",
            ],
            "allow_phrase": "I authorize repo-sentinel changes",
        },
    }


def repo_state_dir(repo: Path) -> Path:
    p = repo / STATE_DIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_state(repo: Path) -> Dict[str, Any]:
    path = repo_state_dir(repo) / "state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "version": 1,
            "touched": {},
            "events": [],
            "last_edit_ts": 0,
            "last_verification_ts": 0,
            "last_verification_command": None,
            "stop_continuations": {},
        }


def write_state(repo: Path, state: Dict[str, Any]) -> None:
    path = repo_state_dir(repo) / "state.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def append_event(repo: Path, event: Dict[str, Any]) -> None:
    path = repo_state_dir(repo) / "events.jsonl"
    event = {"ts": _now(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def relpath(repo: Path, path: str | Path) -> Optional[str]:
    p = Path(path)
    if not p.is_absolute():
        p = (repo / p).resolve()
    else:
        p = p.resolve()
    try:
        rel = p.relative_to(repo.resolve())
        return rel.as_posix()
    except Exception:
        return None


def _norm_glob(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    p = _norm_glob(path)
    for pat in patterns:
        q = _norm_glob(pat)
        if fnmatch.fnmatch(p, q) or fnmatch.fnmatch("./" + p, q):
            return True
        # fnmatch doesn't always treat ** as expected for root files.
        if q.startswith("**/") and fnmatch.fnmatch(p, q[3:]):
            return True
    return False


def override_enabled(policy: Dict[str, Any], key: str) -> bool:
    env = policy.get("overrides", {}).get(key)
    return bool(env and os.environ.get(env))


def deny_output(event: str, reason: str, agent: str = "auto") -> Dict[str, Any]:
    if event == "PermissionRequest":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "deny", "message": reason},
            }
        }
    if event == "PreToolUse":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    if event == "Stop":
        return {"decision": "block", "reason": reason}
    if event == "UserPromptSubmit":
        return {"decision": "block", "reason": reason}
    if event == "ConfigChange":
        return {"decision": "block", "reason": reason}
    if event == "PostToolUse":
        return {
            "decision": "block",
            "reason": reason,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": reason,
            },
        }
    return {"decision": "block", "reason": reason}


def context_output(event: str, text: str) -> Dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}


def emit(obj: Optional[Dict[str, Any]]) -> int:
    if obj:
        print(_json_dumps(obj))
    return 0


def tool_command(data: Dict[str, Any]) -> str:
    ti = data.get("tool_input") or {}
    if isinstance(ti, dict):
        cmd = ti.get("command") or ti.get("cmd") or ti.get("script")
        if isinstance(cmd, str):
            return cmd
    if isinstance(ti, str):
        return ti
    return ""


def extract_paths_from_tool(repo: Path, data: Dict[str, Any]) -> List[str]:
    tool = str(data.get("tool_name") or "")
    ti = data.get("tool_input") or {}
    paths: List[str] = []

    def add_path(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            rp = relpath(repo, value.strip())
            paths.append(rp if rp is not None else value.strip())

    if isinstance(ti, dict):
        for key in ("file_path", "path", "notebook_path"):
            add_path(ti.get(key))
        for key in ("files", "paths"):
            val = ti.get(key)
            if isinstance(val, list):
                for x in val:
                    add_path(x)
        if tool == "apply_patch" or "apply_patch" in tool.lower():
            cmd = ti.get("command", "")
            if isinstance(cmd, str):
                paths.extend(extract_paths_from_patch(repo, cmd))
    elif isinstance(ti, str):
        if tool == "apply_patch":
            paths.extend(extract_paths_from_patch(repo, ti))
    # De-duplicate preserving order.
    seen = set()
    out = []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def extract_paths_from_patch(repo: Path, patch_or_command: str) -> List[str]:
    paths: List[str] = []
    for line in patch_or_command.splitlines():
        line = line.strip()
        for prefix in ("*** Update File:", "*** Add File:", "*** Delete File:"):
            if line.startswith(prefix):
                raw = line[len(prefix) :].strip()
                rp = relpath(repo, raw)
                paths.append(rp if rp is not None else raw)
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            raw = line[6:].strip()
            if raw != "/dev/null":
                rp = relpath(repo, raw)
                paths.append(rp if rp is not None else raw)
    return list(dict.fromkeys(paths))


def is_write_tool(tool_name: str) -> bool:
    t = tool_name.lower()
    return (
        t in {"write", "edit", "multiedit", "notebookedit", "apply_patch"}
        or "write" in t
        or "edit" in t
        or "apply_patch" in t
        or t.startswith("mcp__filesystem__write")
        or t.startswith("mcp__filesystem__edit")
    )


def guard_paths(
    repo: Path, policy: Dict[str, Any], paths: Sequence[str]
) -> Optional[str]:
    if override_enabled(policy, "allow_all_env"):
        return None
    protected = policy.get("protected_paths", [])
    generated = policy.get("generated_paths", [])
    migration = policy.get("migration_guard", {})
    mig_patterns = migration.get("patterns", [])
    protect_existing_migrations = bool(migration.get("protect_existing", True))

    for p in paths:
        rp = relpath(repo, p) if Path(p).is_absolute() else p
        if rp is None:
            return f"Repo Sentinel blocked write outside repository root: {p}"
        rp = _norm_glob(rp)
        if matches_any(
            rp,
            [
                ".repo-sentinel/**",
                ".claude/settings*.json",
                ".claude/hooks/**",
                ".codex/**",
                ".agents/**",
            ],
        ):
            if not override_enabled(policy, "allow_config_change_env"):
                return f"Repo Sentinel blocked modification of agent configuration or sentinel policy path: {rp}. Set the documented override env var only after manual review."
        if matches_any(
            rp,
            [
                ".env",
                ".env.*",
                "**/.env",
                "**/.env.*",
                "**/*secret*",
                "**/*credential*",
                "**/*.pem",
                "**/*.key",
            ],
        ):
            if not override_enabled(policy, "allow_secret_write_env"):
                return f"Repo Sentinel blocked modification of secret-like path: {rp}."
        if matches_any(rp, protected):
            return f"Repo Sentinel blocked write to protected/generated path: {rp}."
        if (
            protect_existing_migrations
            and matches_any(rp, mig_patterns)
            and (repo / rp).exists()
        ):
            return f"Repo Sentinel blocked editing existing migration file: {rp}. Create a new migration instead."
        if matches_any(rp, generated):
            return f"Repo Sentinel blocked write to generated/cache path: {rp}."
    return None


def guard_shell(
    policy: Dict[str, Any], command: str
) -> Tuple[Optional[str], List[str]]:
    if not command:
        return None, []
    if override_enabled(policy, "allow_all_env") or override_enabled(
        policy, "allow_destructive_env"
    ):
        return None, []
    deny_items = policy.get("shell", {}).get("deny_regex", [])
    for item in deny_items:
        try:
            if re.search(item.get("pattern", "$^"), command):
                return (
                    f"Repo Sentinel blocked command ({item.get('name', 'policy')}): {item.get('reason', 'Blocked by policy')}",
                    [],
                )
        except re.error as exc:
            return f"Repo Sentinel policy regex error in {item.get('name')}: {exc}", []
    warnings = []
    for item in policy.get("shell", {}).get("warn_regex", []):
        try:
            if re.search(item.get("pattern", "$^"), command):
                warnings.append(
                    f"{item.get('name', 'warning')}: {item.get('message', 'Review command carefully.')}"
                )
        except re.error:
            pass
    return None, warnings


def file_looks_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except Exception:
        return True
    return b"\x00" in chunk


def scan_file_for_secrets(path: Path, policy: Dict[str, Any]) -> List[str]:
    cfg = policy.get("secret_scan", {})
    if not cfg.get("enabled", True):
        return []
    try:
        if not path.exists() or not path.is_file():
            return []
        if path.stat().st_size > int(cfg.get("max_file_bytes", 1048576)):
            return []
        if file_looks_binary(path):
            return []
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    hits = []
    for item in cfg.get("patterns", []):
        try:
            if re.search(item.get("regex", "$^"), text):
                hits.append(item.get("name", "secret-like pattern"))
        except re.error:
            continue
    return hits


def command_success(data: Dict[str, Any]) -> bool:
    tr = data.get("tool_response")
    if tr is None:
        return False
    if isinstance(tr, dict):
        # Codex-style command output commonly includes exit code/status; Claude-style
        # output can vary, so keep the detection conservative.
        for key in ("exit_code", "exitCode", "returncode", "return_code"):
            if key in tr:
                try:
                    return int(tr[key]) == 0
                except Exception:
                    pass
        status = tr.get("status")
        if isinstance(status, str):
            return status.lower() in {"success", "completed", "ok"}
        if tr.get("success") is True:
            return True
        if tr.get("interrupted") is True:
            return False
        # If Bash returned stdout/stderr without explicit code, do not assume success
        # when stderr contains common failure markers.
        stderr = str(tr.get("stderr", ""))
        if stderr and re.search(
            r"(?i)(error|failed|traceback|command not found)", stderr
        ):
            return False
    return False


def command_is_verification(policy: Dict[str, Any], command: str) -> bool:
    for pat in policy.get("shell", {}).get("verification_success_regex", []):
        try:
            if re.search(pat, command):
                return True
        except re.error:
            continue
    return False


def record_edit(repo: Path, paths: Sequence[str]) -> None:
    if not paths:
        return
    state = read_state(repo)
    ts = _now()
    touched = state.setdefault("touched", {})
    for p in paths:
        touched[_norm_glob(p)] = {"last_edit_ts": ts}
    state["last_edit_ts"] = max(ts, float(state.get("last_edit_ts") or 0))
    write_state(repo, state)
    append_event(repo, {"event": "edit", "paths": list(paths)})


def record_verification(repo: Path, command: str) -> None:
    state = read_state(repo)
    ts = _now()
    state["last_verification_ts"] = ts
    state["last_verification_command"] = command
    write_state(repo, state)
    append_event(repo, {"event": "verification", "command": command})


def changed_files(repo: Path) -> List[str]:
    out: List[str] = []
    code, stdout, _ = _run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo,
        timeout=8,
    )
    if code == 0:
        for line in stdout.splitlines():
            if not line.strip():
                continue
            # Format: XY path or XY old -> new
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            out.append(_norm_glob(path.strip()))
    state = read_state(repo)
    out.extend(state.get("touched", {}).keys())
    return sorted(set(x for x in out if x))


def is_code_change(policy: Dict[str, Any], files: Sequence[str]) -> bool:
    cfg = policy.get("verification", {})
    ignore = cfg.get("ignore_globs", [])
    code_globs = cfg.get("code_globs", [])
    docs_globs = cfg.get("docs_globs", [])
    allow_docs = cfg.get("allow_docs_only_stop", True)
    relevant = [f for f in files if not matches_any(f, ignore)]
    if not relevant:
        return False
    if allow_docs and all(matches_any(f, docs_globs) for f in relevant):
        return False
    return any(matches_any(f, code_globs) for f in relevant) or bool(relevant)


def suggest_checks(repo: Path, files: Sequence[str]) -> List[str]:
    suggestions: List[str] = []

    def exists(name: str) -> bool:
        return (repo / name).exists()

    if (
        exists("pyproject.toml")
        or exists("pytest.ini")
        or exists("setup.cfg")
        or any(f.endswith(".py") for f in files)
    ):
        suggestions.append("python -m pytest")
    if exists("package.json"):
        pm = "npm"
        if exists("pnpm-lock.yaml"):
            pm = "pnpm"
        elif exists("yarn.lock"):
            pm = "yarn"
        elif exists("bun.lockb") or exists("bun.lock"):
            pm = "bun"
        suggestions.append(f"{pm} test")
    if exists("go.mod"):
        suggestions.append("go test ./...")
    if exists("Cargo.toml"):
        suggestions.append("cargo test")
    if exists("pom.xml"):
        suggestions.append("mvn test")
    if exists("build.gradle") or exists("build.gradle.kts"):
        suggestions.append("./gradlew test")
    if exists("Makefile"):
        suggestions.append("make test")
    suggestions.append("python .repo-sentinel/repo_sentinel.py check")
    return list(dict.fromkeys(suggestions))[:4]


def hook_pre_tool(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    if policy.get("__policy_error__"):
        return deny_output("PreToolUse", policy["__policy_error__"], agent)
    tool = str(data.get("tool_name") or "")
    if tool.lower() == "bash":
        cmd = tool_command(data)
        reason, warnings = guard_shell(policy, cmd)
        if reason:
            return deny_output("PreToolUse", reason, agent)
        if warnings:
            return context_output(
                "PreToolUse", "Repo Sentinel warnings: " + "; ".join(warnings)
            )
    if is_write_tool(tool):
        paths = extract_paths_from_tool(repo, data)
        reason = guard_paths(repo, policy, paths)
        if reason:
            return deny_output("PreToolUse", reason, agent)
    return None


def hook_permission_request(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    # Codex-specific additional guard for escalation prompts.
    tool = str(data.get("tool_name") or "")
    if tool.lower() == "bash":
        reason, warnings = guard_shell(policy, tool_command(data))
        if reason:
            return deny_output("PermissionRequest", reason, agent)
        if warnings:
            # Let normal approval prompt continue; no supported context-only shape for PermissionRequest beyond systemMessage.
            return {"systemMessage": "Repo Sentinel warnings: " + "; ".join(warnings)}
    if is_write_tool(tool):
        reason = guard_paths(repo, policy, extract_paths_from_tool(repo, data))
        if reason:
            return deny_output("PermissionRequest", reason, agent)
    return None


def hook_post_tool(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    tool = str(data.get("tool_name") or "")
    if is_write_tool(tool):
        paths = extract_paths_from_tool(repo, data)
        if paths:
            record_edit(repo, paths)
            secret_hits: Dict[str, List[str]] = {}
            for rp in paths:
                rel = relpath(repo, rp) if Path(rp).is_absolute() else rp
                if rel:
                    hits = scan_file_for_secrets(repo / rel, policy)
                    if hits:
                        secret_hits[rel] = hits
            if secret_hits:
                formatted = ", ".join(
                    f"{p} ({'; '.join(h)})" for p, h in secret_hits.items()
                )
                return deny_output(
                    "PostToolUse",
                    f"Repo Sentinel detected secret-like content after edit: {formatted}. Remove or rotate before continuing.",
                    agent,
                )
    if tool.lower() == "bash":
        cmd = tool_command(data)
        if cmd and command_is_verification(policy, cmd) and command_success(data):
            record_verification(repo, cmd)
            return context_output(
                "PostToolUse",
                f"Repo Sentinel recorded successful verification command: {cmd}",
            )
    return None


def hook_user_prompt(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    cfg = policy.get("prompt_guard", {})
    prompt = str(data.get("prompt") or "")
    if cfg.get("enabled", True) and prompt:
        allow_phrase = cfg.get("allow_phrase", "I authorize repo-sentinel changes")
        if allow_phrase not in prompt:
            for pat in cfg.get("block_regex", []):
                try:
                    if re.search(pat, prompt):
                        return deny_output(
                            "UserPromptSubmit",
                            f"Repo Sentinel blocked a prompt that appears to disable or bypass repository guardrails. To change guardrails, use the explicit authorization phrase: {allow_phrase}",
                            agent,
                        )
                except re.error:
                    continue
    summary = summarize_policy(policy)
    return context_output("UserPromptSubmit", summary)


def hook_session_start(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    return context_output("SessionStart", summarize_policy(policy))


def hook_config_change(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    file_path = str(data.get("file_path") or "")
    source = str(data.get("source") or "")
    if override_enabled(policy, "allow_config_change_env") or override_enabled(
        policy, "allow_all_env"
    ):
        return None
    if file_path:
        rp = relpath(repo, file_path)
        if rp and matches_any(
            rp,
            [
                ".claude/settings*.json",
                ".claude/hooks/**",
                ".codex/**",
                ".agents/**",
                ".repo-sentinel/**",
            ],
        ):
            return deny_output(
                "ConfigChange",
                f"Repo Sentinel blocked config change to {rp}. Review manually, then set the documented override env var for one run if intentional.",
                agent,
            )
    if source in {"project_settings", "local_settings", "user_settings"}:
        return deny_output(
            "ConfigChange",
            f"Repo Sentinel blocked live configuration change source={source}. Review hook/MCP/settings changes manually.",
            agent,
        )
    return None


def hook_stop(
    repo: Path, policy: Dict[str, Any], data: Dict[str, Any], agent: str
) -> Optional[Dict[str, Any]]:
    cfg = policy.get("verification", {})
    if not cfg.get("require_on_stop", True):
        return None
    if data.get("stop_hook_active"):
        return None
    files = changed_files(repo)
    if not is_code_change(policy, files):
        return None
    state = read_state(repo)
    last_edit = float(state.get("last_edit_ts") or 0)
    last_ver = float(state.get("last_verification_ts") or 0)
    if last_ver >= last_edit and state.get("last_verification_command"):
        return None
    turn_id = str(data.get("turn_id") or data.get("session_id") or "default")
    max_count = int(cfg.get("max_stop_continuations_per_turn", 1))
    continuations = state.setdefault("stop_continuations", {})
    current = int(continuations.get(turn_id, 0))
    if current >= max_count:
        return None
    continuations[turn_id] = current + 1
    write_state(repo, state)
    suggestions = suggest_checks(repo, files)
    file_preview = ", ".join(files[:8]) + (" ..." if len(files) > 8 else "")
    reason = (
        "Repo Sentinel verification gate: code/config files changed but no successful verification command was recorded after the last edit. "
        f"Changed/touched files: {file_preview}. Run one targeted check, preferably: "
        + " OR ".join(suggestions[:3])
        + ". "
        "After a successful check, summarize the evidence."
    )
    return deny_output("Stop", reason, agent)


def summarize_policy(policy: Dict[str, Any]) -> str:
    mode = policy.get("mode", "strict")
    require_stop = policy.get("verification", {}).get("require_on_stop", True)
    return (
        f"Repo Sentinel active: mode={mode}; destructive shell commands, protected paths, secret-like edits, "
        f"existing migrations, and agent config changes are guarded. Verification on stop={'on' if require_stop else 'off'}. "
        "Use `python .repo-sentinel/repo_sentinel.py check` for a local sentinel check."
    )


def run_hook(args: argparse.Namespace) -> int:
    data = _read_json_stdin()
    repo = find_repo_root(data.get("cwd") or os.getcwd())
    policy = load_policy(repo, args.policy)
    event = str(data.get("hook_event_name") or args.event or "")
    agent = args.agent
    handler = {
        "PreToolUse": hook_pre_tool,
        "PermissionRequest": hook_permission_request,
        "PostToolUse": hook_post_tool,
        "UserPromptSubmit": hook_user_prompt,
        "SessionStart": hook_session_start,
        "ConfigChange": hook_config_change,
        "Stop": hook_stop,
    }.get(event)
    if not handler:
        return 0
    out = handler(repo, policy, data, agent)
    return emit(out)


def check_repo(args: argparse.Namespace) -> int:
    repo = find_repo_root(args.cwd or os.getcwd())
    policy = load_policy(repo, args.policy)
    files = changed_files(repo) if args.changed_only else []
    failures: List[str] = []
    paths_to_scan: List[str] = files
    if not paths_to_scan:
        # Scan likely text files only, cheaply.
        for p in repo.rglob("*"):
            if p.is_file():
                rp = relpath(repo, p)
                if rp and not matches_any(
                    rp, policy.get("verification", {}).get("ignore_globs", [])
                ):
                    paths_to_scan.append(rp)
    for rp in paths_to_scan:
        path_reason = guard_paths(repo, policy, [rp])
        # For check mode, sentinel config paths are expected; don't fail on its own scaffold.
        if path_reason and not rp.startswith(".repo-sentinel/"):
            failures.append(path_reason)
        hits = scan_file_for_secrets(repo / rp, policy)
        if hits:
            failures.append(f"Secret-like content: {rp} ({'; '.join(hits)})")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1
    print("Repo Sentinel check passed.")
    if args.record:
        record_verification(repo, "python .repo-sentinel/repo_sentinel.py check")
    return 0


def status(args: argparse.Namespace) -> int:
    repo = find_repo_root(args.cwd or os.getcwd())
    policy = load_policy(repo, args.policy)
    state = read_state(repo)
    files = changed_files(repo)
    out = {
        "version": VERSION,
        "repo": str(repo),
        "policy_mode": policy.get("mode"),
        "changed_or_touched_files": files,
        "last_edit_ts": state.get("last_edit_ts"),
        "last_verification_ts": state.get("last_verification_ts"),
        "last_verification_command": state.get("last_verification_command"),
        "verification_needed": is_code_change(policy, files)
        and float(state.get("last_verification_ts") or 0)
        < float(state.get("last_edit_ts") or 0),
        "suggested_checks": suggest_checks(repo, files),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Repo Sentinel deterministic repository guardrails"
    )
    parser.add_argument(
        "--version", action="version", version=f"repo-sentinel {VERSION}"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_hook = sub.add_parser("hook", help="Run as a Claude Code or Codex hook")
    p_hook.add_argument("--event", default=None, help="Override hook_event_name")
    p_hook.add_argument("--agent", choices=["auto", "claude", "codex"], default="auto")
    p_hook.add_argument("--policy", default=None)
    p_hook.set_defaults(func=run_hook)

    p_check = sub.add_parser("check", help="Run local policy checks")
    p_check.add_argument("--policy", default=None)
    p_check.add_argument("--cwd", default=None)
    p_check.add_argument("--changed-only", action="store_true", default=True)
    p_check.add_argument("--all", dest="changed_only", action="store_false")
    p_check.add_argument(
        "--record",
        action="store_true",
        help="Record successful sentinel check as verification",
    )
    p_check.set_defaults(func=check_repo)

    p_status = sub.add_parser("status", help="Print sentinel state")
    p_status.add_argument("--policy", default=None)
    p_status.add_argument("--cwd", default=None)
    p_status.set_defaults(func=status)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
