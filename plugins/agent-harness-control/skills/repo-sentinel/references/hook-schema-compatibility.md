# Hook schema compatibility

## Claude Code

Repo Sentinel uses only command hooks. The Claude settings example wires these events:

- `SessionStart` to inject a short policy summary.
- `UserPromptSubmit` to block prompt attempts to bypass hooks.
- `PreToolUse` to block destructive Bash commands and protected writes.
- `PostToolUse` to record edits, scan for secrets, and record successful checks.
- `ConfigChange` to block live hook/settings changes.
- `Stop` to require verification after code edits.

For `PreToolUse`, Repo Sentinel emits:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

For `Stop`, it emits:

```json
{"decision":"block","reason":"..."}
```

## Codex

Repo Sentinel uses Codex command hooks only. Codex currently parses but does not execute prompt/agent hook handlers, so this pack avoids them.

Codex-specific additions:

- `PermissionRequest` hook for escalation prompts.
- `.codex/rules/repo-sentinel.rules` for execpolicy checks.
- `.agents/skills/repo-sentinel/SKILL.md` for local Codex skill discovery.

For `PermissionRequest`, Repo Sentinel emits:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {"behavior": "deny", "message": "..."}
  }
}
```

## Shared core

Both agents call the same script:

```bash
python3 .repo-sentinel/repo_sentinel.py hook --agent claude
python3 .repo-sentinel/repo_sentinel.py hook --agent codex
```

The script reads hook JSON from stdin and decides based on `hook_event_name`, `tool_name`, `tool_input`, `tool_response`, and `cwd`.

The scaffold uses `python3` in hook commands because target repositories may not use `uv`. For manual validation inside uv-managed repositories, prefer `uv run python .repo-sentinel/repo_sentinel.py ...`.
