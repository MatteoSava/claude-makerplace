# Hook schema compatibility

## Claude Code

AgentOps uses these Claude Code hook events:

- `SessionStart`: inject continuity context when a session starts, resumes, clears, or resumes after compact.
- `UserPromptSubmit`: update the current task and inject relevant state before the prompt is processed.
- `PreToolUse`: record intended touched files and protect AgentOps state from accidental deletion.
- `PostToolUse`: record successful edits/checks and auto-detect verification commands.
- `PostToolUseFailure`: record failed verification commands.
- `PostToolBatch`: inject one compact reminder after a batch of tools.
- `Stop`: require verification before final response when policy says so.
- `PreCompact`: snapshot local state before compaction.
- `PostCompact`: save `compact_summary` to the ledger.
- `SessionEnd`: write a final snapshot.
- `ConfigChange`: audit configuration changes.

Claude `PreCompact` can block compaction, but this package does not block by default. Claude `PostCompact` has no decision control, so the package records compact summaries and relies on later `SessionStart`/`UserPromptSubmit` context injection.

## Codex

AgentOps uses the Codex hook events currently useful for this purpose:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `Stop`

Codex does not provide a package-level equivalent to Claude `PreCompact`/`PostCompact` here. Codex continuity therefore depends on the same ledger plus startup/prompt/stop hooks.

Codex currently runs command hooks; prompt and agent hook handlers may be parsed but should not be relied on as executable handlers.
