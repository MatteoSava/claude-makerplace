#!/usr/bin/env python3
"""Deterministic WebQA DevTools hook helper for Claude Code and Codex.

This script is intentionally dependency-free. It tracks frontend edits, records
Chrome DevTools MCP evidence, blocks unsafe browser actions by policy, and can
block Stop until required browser evidence exists.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
BASE = SCRIPT.parent
STATE_DIR = BASE / "state"
REPORTS_DIR = BASE / "reports"
ARTIFACTS_DIR = BASE / "artifacts"
STATE_FILE = STATE_DIR / "state.json"
POLICY_FILE = BASE / "policy.json"
LOG_FILE = STATE_DIR / "events.jsonl"

DEFAULT_STATE: dict[str, Any] = {
    "dirty_frontend": False,
    "last_frontend_change_at": None,
    "touched_frontend_files": [],
    "browser_evidence": [],
    "verification_commands": [],
    "manual_verifications": [],
    "reports": [],
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return json.loads(json.dumps(default))


def save_json(path: Path, data: Any) -> None:
    ensure_dirs()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_policy() -> dict[str, Any]:
    return load_json(POLICY_FILE, {})


def load_state() -> dict[str, Any]:
    state = load_json(STATE_FILE, DEFAULT_STATE)
    merged = json.loads(json.dumps(DEFAULT_STATE))
    merged.update(state)
    return merged


def save_state(state: dict[str, Any]) -> None:
    save_json(STATE_FILE, state)


def log_event(kind: str, payload: dict[str, Any]) -> None:
    ensure_dirs()
    entry = {"at": now(), "kind": kind, "payload": payload}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def emit_json(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, indent=2))


def hook_context(text: str, event_name: str | None = None) -> dict[str, Any]:
    obj: dict[str, Any] = {"additionalContext": text}
    if event_name:
        obj["hookSpecificOutput"] = {
            "hookEventName": event_name,
            "additionalContext": text,
        }
    return obj


def deny_pretool(reason: str, event_name: str = "PreToolUse") -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def block_stop(reason: str) -> dict[str, Any]:
    return {"decision": "block", "reason": reason}


def rel_path(path: str | Path) -> str:
    p = Path(path)
    try:
        if p.is_absolute():
            return str(p.resolve().relative_to(ROOT))
        return str(p)
    except Exception:
        return str(p)


def normalize_paths(paths: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in paths:
        if not item:
            continue
        item = item.strip().strip("\"'")
        if not item:
            continue
        out.append(rel_path(item))
    return sorted(set(out))


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        p = str(pattern).replace("\\", "/")
        if fnmatch.fnmatch(normalized, p) or fnmatch.fnmatch("./" + normalized, p):
            return True
    return False


def is_frontend_file(path: str, policy: dict[str, Any]) -> bool:
    if not path or path.startswith(".webqa-devtools/"):
        return False
    excludes = policy.get("frontend_exclude_globs", [])
    if matches_any(path, excludes):
        return False
    globs = policy.get("frontend_file_globs", [])
    return matches_any(path, globs)


def extract_paths_from_patch(command: str) -> list[str]:
    paths: list[str] = []
    regexes = [
        r"^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(.+)$",
        r"^---\s+a/(.+)$",
        r"^\+\+\+\s+b/(.+)$",
    ]
    for line in command.splitlines():
        for rx in regexes:
            m = re.search(rx, line.strip())
            if m:
                paths.append(m.group(1).strip())
    return normalize_paths(paths)


def extract_tool_paths(tool_name: str, tool_input: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "notebook_path", "filePath"):
            val = tool_input.get(key)
            if isinstance(val, str):
                paths.append(val)
        if "edits" in tool_input and isinstance(tool_input["edits"], list):
            # MultiEdit usually has one file_path plus list of edits; handled above.
            pass
        command = tool_input.get("command")
        if isinstance(command, str):
            if (
                tool_name in {"apply_patch", "Patch"}
                or "apply_patch" in command
                or "*** Begin Patch" in command
            ):
                paths.extend(extract_paths_from_patch(command))
    elif isinstance(tool_input, str):
        paths.extend(extract_paths_from_patch(tool_input))
    return normalize_paths(paths)


def tool_short_name(tool_name: str) -> str:
    # mcp__chrome-devtools__take_snapshot -> take_snapshot
    if "__" in tool_name:
        return tool_name.split("__")[-1]
    if ":" in tool_name:
        return tool_name.split(":")[-1]
    return tool_name


def is_chrome_devtools_tool(tool_name: str) -> bool:
    lower = tool_name.lower()
    known = {
        "click",
        "drag",
        "fill",
        "fill_form",
        "handle_dialog",
        "hover",
        "press_key",
        "type_text",
        "upload_file",
        "click_at",
        "close_page",
        "list_pages",
        "navigate_page",
        "new_page",
        "select_page",
        "wait_for",
        "emulate",
        "resize_page",
        "performance_analyze_insight",
        "performance_start_trace",
        "performance_stop_trace",
        "get_network_request",
        "list_network_requests",
        "evaluate_script",
        "get_console_message",
        "lighthouse_audit",
        "list_console_messages",
        "take_screenshot",
        "take_snapshot",
        "screencast_start",
        "screencast_stop",
    }
    return (
        "chrome-devtools" in lower
        or "chrome_devtools" in lower
        or tool_short_name(tool_name) in known
    )


def evidence_category(tool_name: str, policy: dict[str, Any]) -> str | None:
    short = tool_short_name(tool_name)
    for category, tools in policy.get("browser_evidence_tools", {}).items():
        if short in tools:
            return category
    return None


def record_frontend_dirty(paths: list[str], source: str) -> None:
    if not paths:
        return
    state = load_state()
    touched = set(state.get("touched_frontend_files", []))
    touched.update(paths)
    state["dirty_frontend"] = True
    state["last_frontend_change_at"] = now()
    state["touched_frontend_files"] = sorted(touched)
    save_state(state)
    log_event("frontend_dirty", {"source": source, "paths": paths})


def record_browser_evidence(
    tool_name: str, tool_input: Any, category: str | None
) -> None:
    state = load_state()
    short = tool_short_name(tool_name)
    summary = {}
    if isinstance(tool_input, dict):
        for key in (
            "url",
            "filePath",
            "requestFilePath",
            "responseFilePath",
            "device",
            "mode",
            "fullPage",
            "types",
            "resourceTypes",
        ):
            if key in tool_input:
                summary[key] = tool_input[key]
    item = {
        "at": now(),
        "tool": short,
        "category": category or "other",
        "input": summary,
    }
    state.setdefault("browser_evidence", []).append(item)
    save_state(state)
    log_event("browser_evidence", item)


def record_verification_command(command: str) -> None:
    state = load_state()
    item = {"at": now(), "command": command[:500]}
    state.setdefault("verification_commands", []).append(item)
    save_state(state)
    log_event("verification_command", item)


def record_manual_verification(kind: str, note: str) -> None:
    state = load_state()
    item = {"at": now(), "kind": kind, "note": note}
    state.setdefault("manual_verifications", []).append(item)
    # Manual verification satisfies evidence gates if the user/agent explicitly records it.
    if kind in {"manual", "not-applicable", "browser"}:
        state["dirty_frontend"] = False
    save_state(state)
    log_event("manual_verification", item)


def command_matches_verification(command: str, policy: dict[str, Any]) -> bool:
    for rx in policy.get("verification_command_regexes", []):
        try:
            if re.search(rx, command):
                return True
        except re.error:
            continue
    return False


def url_allowed(url: str, policy: dict[str, Any]) -> tuple[bool, str]:
    if not url:
        return True, ""
    parsed = urlparse(url)
    if not parsed.scheme:
        return True, "relative URL"
    for rx in policy.get("blocked_url_regexes", []):
        try:
            if re.search(rx, url):
                return False, f"URL matches blocked pattern: {rx}"
        except re.error:
            continue
    if policy.get("allow_external_urls", False):
        return True, "external URLs allowed by policy"
    allowed_prefixes = policy.get("allowed_url_prefixes", [])
    if any(url.startswith(prefix) for prefix in allowed_prefixes):
        return True, "allowed local prefix"
    return (
        False,
        "Chrome DevTools navigation is restricted to local URLs by .webqa-devtools/policy.json",
    )


def contains_sensitive_headers(tool_input: Any) -> bool:
    if not isinstance(tool_input, dict):
        return False
    headers = tool_input.get("extraHttpHeaders")
    if not headers:
        return False
    text = headers if isinstance(headers, str) else json.dumps(headers)
    return bool(
        re.search(
            r"(?i)(authorization|bearer|api[_-]?key|secret|token|cookie|session)", text
        )
    )


def artifact_path_allowed(file_path: str, policy: dict[str, Any]) -> tuple[bool, str]:
    if not file_path or not policy.get("restrict_artifact_paths", True):
        return True, ""
    try:
        p = Path(file_path)
        resolved = p.resolve() if p.is_absolute() else (ROOT / p).resolve()
        root_resolved = ROOT.resolve()
        resolved.relative_to(root_resolved)
    except Exception:
        return False, "Browser artifact path must be inside the repository"
    rel = str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    allowed_dirs = [
        str(x).replace("\\", "/").rstrip("/")
        for x in policy.get("allowed_artifact_dirs", [])
    ]
    if any(rel == d or rel.startswith(d + "/") for d in allowed_dirs):
        return True, ""
    return (
        False,
        f"Browser artifact path '{rel}' is outside allowed artifact dirs: {', '.join(allowed_dirs)}",
    )


def pre_tool_policy(
    event: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any] | None:
    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})

    if is_chrome_devtools_tool(tool_name) and isinstance(tool_input, dict):
        short = tool_short_name(tool_name)

        # URL navigation guard.
        if short in {"navigate_page", "new_page"}:
            url = str(tool_input.get("url") or "")
            ok, reason = url_allowed(url, policy)
            if not ok:
                return deny_pretool(
                    f"Blocked Chrome DevTools navigation to {url!r}. {reason}"
                )

        # Header guard.
        if (
            short == "emulate"
            and contains_sensitive_headers(tool_input)
            and not policy.get("allow_sensitive_headers", False)
        ):
            return deny_pretool(
                "Blocked DevTools emulate call with sensitive HTTP headers. Use test tokens only and update policy if this is intentional."
            )

        # Artifact path guard.
        for key in ("filePath", "requestFilePath", "responseFilePath", "outputDirPath"):
            val = tool_input.get(key)
            if isinstance(val, str) and val:
                ok, reason = artifact_path_allowed(val, policy)
                if not ok:
                    return deny_pretool(reason)

        # Upload guard: file uploads can leak local files.
        if short == "upload_file":
            val = str(tool_input.get("filePath") or "")
            ok, reason = artifact_path_allowed(
                val,
                {
                    **policy,
                    "allowed_artifact_dirs": policy.get("allowed_upload_dirs", []),
                },
            )
            if not ok:
                return deny_pretool(
                    "Blocked browser file upload from an unapproved path. Configure allowed_upload_dirs if this is intentional."
                )

    return None


def handle_post_tool(event: dict[str, Any], policy: dict[str, Any]) -> None:
    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    paths = extract_tool_paths(tool_name, tool_input)
    frontend = [p for p in paths if is_frontend_file(p, policy)]
    if frontend:
        record_frontend_dirty(frontend, source=tool_name)

    if (
        isinstance(tool_input, dict)
        and "command" in tool_input
        and isinstance(tool_input["command"], str)
    ):
        command = tool_input["command"]
        if command_matches_verification(command, policy):
            record_verification_command(command)

    if is_chrome_devtools_tool(tool_name):
        cat = evidence_category(tool_name, policy)
        if cat:
            record_browser_evidence(tool_name, tool_input, cat)


def evidence_after(ts: str | None, state: dict[str, Any]) -> list[dict[str, Any]]:
    if not ts:
        return state.get("browser_evidence", [])
    return [e for e in state.get("browser_evidence", []) if str(e.get("at", "")) >= ts]


def verification_after(ts: str | None, state: dict[str, Any]) -> list[dict[str, Any]]:
    if not ts:
        return state.get("verification_commands", [])
    return [
        e for e in state.get("verification_commands", []) if str(e.get("at", "")) >= ts
    ]


def stop_gate(policy: dict[str, Any]) -> dict[str, Any] | None:
    state = load_state()
    if not state.get("dirty_frontend"):
        return None

    changed_at = state.get("last_frontend_change_at")
    touched = state.get("touched_frontend_files", [])
    reasons: list[str] = []

    if policy.get("require_browser_evidence_after_frontend_changes", True):
        ev = evidence_after(changed_at, state)
        categories = {e.get("category") for e in ev}
        missing = [
            c
            for c in policy.get("minimum_browser_evidence_categories", [])
            if c not in categories
        ]
        if missing:
            reasons.append(
                "missing browser evidence categories after the latest frontend change: "
                + ", ".join(missing)
            )

    if policy.get("require_test_or_build_after_frontend_changes", False):
        if not verification_after(changed_at, state):
            reasons.append(
                "missing build/test/lint command after the latest frontend change"
            )

    if reasons:
        file_list = ", ".join(touched[:8]) + (" ..." if len(touched) > 8 else "")
        reason = (
            "WebQA DevTools stop gate: frontend/UI files changed but verification is incomplete. "
            f"Touched: {file_list or 'unknown'}. "
            + "; ".join(reasons)
            + ". Continue by verifying the local app with Chrome DevTools MCP: navigate to the route, take_snapshot or screenshot, list console messages, and inspect network requests when relevant. "
            + "Then save a report under .webqa-devtools/reports/ or record a justified manual verification with: "
            + "python .webqa-devtools/webqa_devtools.py mark-verified --kind manual --note '<reason>'."
        )
        return block_stop(reason)

    # Verification satisfied; clear dirty bit but keep touched file history.
    state["dirty_frontend"] = False
    save_state(state)
    return None


def context_summary(policy: dict[str, Any]) -> str:
    state = load_state()
    dirty = "yes" if state.get("dirty_frontend") else "no"
    project_url = policy.get("project_url", "http://localhost:3000")
    touched = state.get("touched_frontend_files", [])
    recent = ", ".join(touched[-5:]) if touched else "none"
    return (
        "WebQA DevTools context:\n"
        f"- Project URL hint: {project_url}\n"
        f"- Frontend dirty: {dirty}\n"
        f"- Recent frontend files: {recent}\n"
        "- If UI/frontend files are changed, verify with Chrome DevTools MCP before finishing. "
        "Collect DOM/visual evidence and runtime console evidence; inspect network when relevant.\n"
        "- Use .webqa-devtools/reports/ for evidence reports. Avoid external or sensitive URLs unless policy/user explicitly permits it."
    )


def handle_hook() -> int:
    ensure_dirs()
    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    event_name = str(event.get("hook_event_name") or event.get("event") or "")
    policy = load_policy()

    if event_name in {"SessionStart", "UserPromptSubmit"}:
        emit_json(hook_context(context_summary(policy), event_name))
        return 0

    if event_name in {"PreToolUse", "PermissionRequest"}:
        result = pre_tool_policy(event, policy)
        if result:
            emit_json(result)
        return 0

    if event_name in {"PostToolUse", "PostToolUseFailure"}:
        handle_post_tool(event, policy)
        return 0

    if event_name == "Stop":
        result = stop_gate(policy)
        if result:
            emit_json(result)
        else:
            emit_json({})
        return 0

    # Unknown/no-op events.
    return 0


def preflight() -> int:
    policy = load_policy()
    print("WebQA DevTools preflight")
    print("- Repo root:", ROOT)
    print("- Policy:", POLICY_FILE if POLICY_FILE.exists() else "missing")
    print("- Project URL hint:", policy.get("project_url", "not set"))
    for cmd in ("node", "npm", "npx", "python"):
        found = shutil.which(cmd)
        print(f"- {cmd}:", found or "not found")
    print("- Chrome DevTools MCP install hints:")
    print(
        "  Claude: claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest"
    )
    print("  Codex:  codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest")
    state = load_state()
    print("- Frontend dirty:", state.get("dirty_frontend"))
    return 0


def status() -> int:
    state = load_state()
    policy = load_policy()
    print("WebQA DevTools status")
    print("- dirty_frontend:", state.get("dirty_frontend"))
    print("- last_frontend_change_at:", state.get("last_frontend_change_at"))
    print("- project_url:", policy.get("project_url"))
    print("- touched_frontend_files:")
    for p in state.get("touched_frontend_files", [])[-20:]:
        print("  -", p)
    print("- browser_evidence:")
    for e in state.get("browser_evidence", [])[-10:]:
        print(f"  - {e.get('at')} {e.get('category')} {e.get('tool')}")
    print("- verification_commands:")
    for e in state.get("verification_commands", [])[-10:]:
        print(f"  - {e.get('at')} {e.get('command')}")
    return 0


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text[:80] or "webqa-report"


def write_report(title: str, result: str = "Partial") -> Path:
    ensure_dirs()
    state = load_state()
    policy = load_policy()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPORTS_DIR / f"{stamp}-{slugify(title)}.md"
    evidence_lines = []
    for e in state.get("browser_evidence", [])[-20:]:
        evidence_lines.append(
            f"- {e.get('at')} `{e.get('category')}` via `{e.get('tool')}` {json.dumps(e.get('input', {}), sort_keys=True)}"
        )
    verification_lines = []
    for e in state.get("verification_commands", [])[-10:]:
        verification_lines.append(f"- {e.get('at')} `{e.get('command')}`")
    touched_lines = [f"- `{p}`" for p in state.get("touched_frontend_files", [])]
    content = f"""# WebQA Report: {title}

- Date: {now()}
- App URL: {policy.get("project_url", "")}
- Result: {result}

## Files changed

{chr(10).join(touched_lines) if touched_lines else "- None recorded"}

## Browser evidence

{chr(10).join(evidence_lines) if evidence_lines else "- None recorded"}

## Verification commands

{chr(10).join(verification_lines) if verification_lines else "- None recorded"}

## Findings

- Fill in observed pass/fail conditions, console/network findings, visual issues, and accessibility/performance notes.

## Remaining risks

- Fill in any unverified routes, browsers, devices, roles, or data states.
"""
    path.write_text(content, encoding="utf-8")
    state.setdefault("reports", []).append(
        {"at": now(), "path": rel_path(path), "title": title, "result": result}
    )
    save_state(state)
    print(path)
    return path


def reset() -> int:
    save_state(json.loads(json.dumps(DEFAULT_STATE)))
    log_event("reset", {})
    print("Reset WebQA DevTools state")
    return 0


def mark_dirty(paths: list[str]) -> int:
    policy = load_policy()
    frontend = [p for p in normalize_paths(paths) if is_frontend_file(p, policy)]
    record_frontend_dirty(frontend, source="manual")
    print(
        "Marked frontend dirty:",
        ", ".join(frontend) if frontend else "no matching frontend files",
    )
    return 0


def mark_verified(kind: str, note: str) -> int:
    record_manual_verification(kind, note)
    print(f"Recorded {kind} verification: {note}")
    return 0


def simulate_hook(path: str | None, command: str | None) -> int:
    event: dict[str, Any] = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {},
    }
    if path:
        event["tool_input"]["file_path"] = path
    if command:
        event["tool_name"] = "Bash"
        event["tool_input"] = {"command": command}
    sys.stdin = type("S", (), {"read": lambda self: json.dumps(event)})()  # type: ignore
    return handle_hook()


def main() -> int:
    parser = argparse.ArgumentParser(description="WebQA DevTools hook helper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hook")
    sub.add_parser("preflight")
    sub.add_parser("status")
    sub.add_parser("reset")
    p_report = sub.add_parser("report")
    p_report.add_argument("--title", default="webqa verification")
    p_report.add_argument(
        "--result", default="Partial", choices=["Pass", "Fail", "Partial"]
    )
    p_dirty = sub.add_parser("mark-dirty")
    p_dirty.add_argument("paths", nargs="+")
    p_verified = sub.add_parser("mark-verified")
    p_verified.add_argument(
        "--kind", default="manual", choices=["manual", "not-applicable", "browser"]
    )
    p_verified.add_argument("--note", required=True)
    p_sim = sub.add_parser("simulate")
    p_sim.add_argument("--path")
    p_sim.add_argument("--command")
    args = parser.parse_args()

    if args.cmd == "hook":
        return handle_hook()
    if args.cmd == "preflight":
        return preflight()
    if args.cmd == "status":
        return status()
    if args.cmd == "reset":
        return reset()
    if args.cmd == "report":
        write_report(args.title, args.result)
        return 0
    if args.cmd == "mark-dirty":
        return mark_dirty(args.paths)
    if args.cmd == "mark-verified":
        return mark_verified(args.kind, args.note)
    if args.cmd == "simulate":
        return simulate_hook(args.path, args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
