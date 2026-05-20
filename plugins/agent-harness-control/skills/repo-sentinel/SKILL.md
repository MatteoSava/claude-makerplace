---
name: repo-sentinel
description: Use when the user wants repository-level agent guardrails, Claude Code or Codex hooks, destructive-command blocking, protected-path policy, secret scanning, verification-before-stop gates, or Repo Sentinel policy tuning/debugging.
---

# Repo Sentinel

Repo Sentinel is a deterministic hook pack for repositories. It adds a local policy layer around agent tool use:

- `PreToolUse` command checks for destructive shell commands and protected writes.
- `PostToolUse` records touched files, verification commands, and secret-scan findings.
- `Stop` blocks completion after code edits when verification is stale.
- Project scaffolds cover Claude Code hooks, Codex hooks, Codex execpolicy rules, and instruction snippets.

## When to use

Use this skill when the user asks to:

- add deterministic guardrails to a repository;
- configure Claude Code or Codex hooks;
- block risky agent commands or file edits;
- enforce tests/lint/checks before an agent stops;
- debug why a Repo Sentinel hook blocked an action;
- tune `.repo-sentinel/policy.json`.

Do not use it as a substitute for code review, dependency scanning, or cloud IAM policy. It is a local deterministic guardrail layer for agent runs.

## Install workflow

For a repository-level install, run from the target repository root. If `CLAUDE_SKILL_DIR` is unavailable, replace it with the absolute path to this skill directory.

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/install.py" --target /path/to/repo --claude --codex
```

This creates a project scaffold containing `.repo-sentinel/`, Claude hook settings example, Codex hooks, Codex execpolicy rules, and optional instruction snippets.

After installing, review these files manually before trusting them:

```text
.repo-sentinel/policy.json
.claude/settings.repo-sentinel.example.json
.codex/hooks.json
.codex/rules/repo-sentinel.rules
.agents/skills/repo-sentinel/SKILL.md
AGENTS.repo-sentinel.md
CLAUDE.repo-sentinel.md
```

For install details and simulation commands, read `references/install-and-operations.md`.

## Claude Code activation

Merge `.claude/settings.repo-sentinel.example.json` into `.claude/settings.json` or copy the `hooks` block. Then run `/hooks` in Claude Code and verify the hook entries.

## Codex activation

Codex reads project hooks from `.codex/hooks.json` when hooks are enabled and the project config layer is trusted. Codex skills can also be installed under `.agents/skills/repo-sentinel/`. Execpolicy rules live under `.codex/rules/`.

Use `references/hook-schema-compatibility.md` when adapting hook event coverage or output JSON for Claude Code vs Codex.

## Standard operating loop

1. Read `uv run python .repo-sentinel/repo_sentinel.py status` when `uv` is available, or use the target repo's configured Python runner.
2. Make the smallest safe change.
3. Let `PreToolUse` block destructive commands or protected writes.
4. Let `PostToolUse` record touched files and successful verification commands.
5. Before stopping, run targeted checks if Repo Sentinel says verification is stale.
6. Summarize the checks and any policy exceptions.

Use `references/policy-reference.md` for policy keys and `references/threat-model.md` for what the guardrails are designed to catch. Use `references/reviewer-roles.md` when the user asks for a manual review role around a blocked action, verification failure, or policy change.

## Override discipline

Do not set override environment variables unless the user explicitly authorizes the change and the action has been manually reviewed. Overrides are intentionally named and narrow:

```text
REPO_SENTINEL_ALLOW_ALL
REPO_SENTINEL_ALLOW_DESTRUCTIVE
REPO_SENTINEL_ALLOW_CONFIG_CHANGE
REPO_SENTINEL_ALLOW_SECRET_WRITE
```

Use them for one command only, then unset them.
