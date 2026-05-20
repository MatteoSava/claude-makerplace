---
name: agentops-continuity
description: Use when a Claude Code, Codex, or OpenCode repository session spans many tool calls, context compaction, handoff, CI/debug loops, multiple skills, task state recovery, stop gates, or verification continuity.
---

# AgentOps Continuity

Use this skill to keep an engineering session coherent across long turns, context compaction, restarts, and handoffs.

## Core idea

Treat `.agentops-continuity/state/` as an operational ledger, not as a replacement for source control or human review.

State files:

- `current-task.json`: current objective, status, touched files, verification requirement.
- `session-ledger.md`: append-only session chronology.
- `context-essentials.md`: curated facts that should survive compaction.
- `decisions.md`: important technical and workflow decisions.
- `open-risks.md`: known risks and unresolved questions.
- `next-actions.md`: queued next actions.
- `compact-summaries.jsonl` and `latest-compact-summary.md`: Claude Code compaction recovery.
- `verification-status.json`: latest explicit verification evidence.

## Install workflow

For a repository-level install, run from the target repository root. If `CLAUDE_SKILL_DIR` is unavailable, replace it with the absolute path to this skill directory.

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/install_agentops_continuity.py" --target /path/to/repo --claude --codex --opencode
```

This copies `.agentops-continuity/`, Claude, Codex, and OpenCode examples, local skill adapters, state templates, and instruction snippets. OpenCode does not have a direct Stop hook equivalent; use the installed OpenCode agents and explicit `status`, `context`, and `mark-verified` commands for the same workflow. Review generated files before enabling hooks.

## Operating rules

1. At the start of a multi-step task, create or confirm a current task:

   ```bash
   python .agentops-continuity/agentops_continuity.py new-task --verification-required "<objective>"
   ```

2. When you make a durable decision, record it:

   ```bash
   python .agentops-continuity/agentops_continuity.py decision --text "Use X because Y; rejected Z because W."
   ```

3. When a risk remains open, record it:

   ```bash
   python .agentops-continuity/agentops_continuity.py risk --text "Risk: ... Mitigation: ..."
   ```

4. Before final response, verify changes. The hooks auto-detect common successful verification commands such as `pytest`, `npm test`, `ruff check`, `mypy`, `go test`, `cargo test`, `terraform plan`, and similar checks.

5. If verification does not apply, mark it explicitly:

   ```bash
   python .agentops-continuity/agentops_continuity.py mark-verified --kind not-applicable --note "Only generated a planning document; no code/config changed."
   ```

6. After compaction or resume, read the injected AgentOps context before continuing. Prefer newer user instructions over stale ledger entries.

## Manual commands

```bash
python .agentops-continuity/agentops_continuity.py status
python .agentops-continuity/agentops_continuity.py context
python .agentops-continuity/agentops_continuity.py snapshot --label before-risky-refactor
python .agentops-continuity/agentops_continuity.py allow-stop --reason "Human approved final response without verification."
python .agentops-continuity/agentops_continuity.py doctor
```

## Handoff protocol

When handing work to another subagent or tool:

- Include current objective.
- Include touched files.
- Include latest verification status.
- Include the smallest relevant ledger excerpt.
- Ask the subagent to write back decisions, risks, and verification evidence.

## Anti-patterns

- Do not paste the entire ledger into normal answers.
- Do not mark verification as passed unless a real check ran successfully.
- Do not use `allow-stop` as a routine bypass.
- Do not let stale compact summaries override fresh code inspection.
