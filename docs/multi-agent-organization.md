# Multi-Agent Organization

Claude Makerplace follows the same separation that works well in Claude Code:
capabilities are split into skills, commands, agents, hooks, and scripts instead
of a single large instruction file.

## Roles

- Main agent: coordinates, owns integration, resolves conflicts, and reports validation.
- Auditor agents: read-only review for package readiness, sanitization, and drift.
- Curator agents: narrowly scoped edits to impacted skills or adjacent package files.
- Quality agents: focused validation for Python tooling and test coverage.

## Delegation Rules

- Delegate broad exploration when it would flood the main context.
- Keep write ownership explicit and narrow.
- Run independent validation after risky packaging or code changes.
- Keep unfinished follow-up work in `TODO.md`.
- Prefer source-of-truth reuse over duplicated prompts.

## Adapter Mapping

| Surface | Source |
|---|---|
| Claude Code | `.claude-plugin/marketplace.json`, `plugins/*/.claude-plugin/plugin.json`, plugin-local `skills/`, `commands/`, `agents/`, `hooks/` |
| Codex | `.agents/plugins/marketplace.json`, `plugins/*/.codex-plugin/plugin.json`, plugin-local command hooks when enabled, optional project `.codex/hooks.json` |
| OpenCode | `opencode.json`, `.opencode/plugins/claude-makerplace.js`, `.opencode/skills`, `.opencode/commands`, `.opencode/agents`, installable `@claude-makerplace/opencode-plugin` package |
