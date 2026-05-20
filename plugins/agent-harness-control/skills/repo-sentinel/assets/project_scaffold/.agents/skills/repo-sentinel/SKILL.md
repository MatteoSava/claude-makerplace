---
name: repo-sentinel
description: Deterministic repository guardrails for Codex. Use when checking, explaining, installing, tuning, or debugging Repo Sentinel hooks, execpolicy rules, protected paths, secret scanning, and verification gates.
---

# Repo Sentinel for Codex

Use this skill when the user asks about repository guardrails, safe command execution, hook failures, verification gates, or policy tuning.

## Operating procedure

1. Inspect `.repo-sentinel/policy.json`, `.codex/hooks.json`, `.codex/rules/repo-sentinel.rules`, and `AGENTS.md`/`AGENTS.repo-sentinel.md`.
2. Use deterministic commands before editing policy:
   - `python .repo-sentinel/repo_sentinel.py status`
   - `python .repo-sentinel/repo_sentinel.py check --record`
   - `codex execpolicy check --pretty --rules .codex/rules/repo-sentinel.rules -- <command>` when available.
3. Do not weaken guardrails silently. If the task requires changing `.repo-sentinel/`, `.codex/`, `.agents/`, or `.claude/`, ask for explicit authorization text first: `I authorize repo-sentinel changes`.
4. After code edits, run a relevant verification command and report evidence.

## Boundaries

Prefer policy changes over ad-hoc bypasses. Temporary bypass env vars should be used only for one manually reviewed run and then removed.
