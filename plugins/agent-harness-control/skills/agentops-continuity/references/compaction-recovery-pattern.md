# Compaction recovery pattern

AgentOps treats compaction as a lossy compression event and keeps a parallel state channel.

## Before compaction

`PreCompact` writes a local snapshot containing:

- active task
- verification status
- touched files
- curated context essentials
- decisions
- open risks
- next actions
- ledger tail

## After compaction

`PostCompact` stores Claude's generated `compact_summary` in:

- `state/compact-summaries.jsonl`
- `state/latest-compact-summary.md`
- `state/session-ledger.md`

`PostCompact` cannot alter compaction output. Recovery happens on later `SessionStart` and `UserPromptSubmit`, where AgentOps injects a compact state block.

## Good compact state

Keep `context-essentials.md` focused on facts that would be expensive or risky to rediscover:

- active architecture choices
- invariants
- user preferences
- special verification commands
- high-risk paths
- external system assumptions

Do not copy entire logs or huge file excerpts.
