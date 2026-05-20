# Hook schema compatibility

WebQA DevTools uses one Python hook core for Claude Code and Codex. The script reads JSON from stdin and emits small JSON decisions.

## Shared events

- `SessionStart`: inject WebQA state/context.
- `UserPromptSubmit`: remind the agent of browser verification rules.
- `PreToolUse`: deny risky Chrome DevTools MCP calls such as external navigation.
- `PostToolUse`: record frontend edits, browser evidence, and verification commands.
- `Stop`: continue/block the agent when required browser evidence is missing.

## Claude Code shape

- `PreToolUse` denies by returning `hookSpecificOutput.permissionDecision = "deny"`.
- `Stop` blocks completion by returning top-level `decision = "block"` and `reason`.
- Context-injection hooks return both top-level `additionalContext` and `hookSpecificOutput.additionalContext` for broad compatibility.

## Codex shape

- This pack uses command hooks only.
- `PreToolUse` can deny supported calls with the same `hookSpecificOutput.permissionDecision = "deny"` shape.
- `Stop` can continue the agent with top-level `decision = "block"` and `reason`.

## Design principle

Do not put browser test logic in deterministic hooks. Hooks only enforce policy, update state, and block unsafe or incomplete work. The skill/subagents perform browser investigation.
