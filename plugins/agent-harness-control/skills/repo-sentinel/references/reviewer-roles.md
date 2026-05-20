# Repo Sentinel Reviewer Roles

Use these as lightweight review checklists when a Repo Sentinel finding needs human judgment.

## Security reviewer

Use for blocked destructive commands, secret-like edits, MCP filesystem operations, and proposed policy exceptions.

1. Identify the exact blocked action and target path/resource.
2. Decide whether the action is necessary and reversible.
3. Suggest the least-powerful safe alternative.
4. If an override is unavoidable, scope it to one command and require cleanup.

## Verification auditor

Use when the Stop hook blocks completion because verification is stale.

1. Read `uv run python .repo-sentinel/repo_sentinel.py status` when `uv` is available.
2. Identify changed files and map them to the smallest relevant checks.
3. Run one or more targeted checks.
4. If checks fail, fix or report the failure with evidence.
5. If checks pass, summarize exact command and result.

## Config guardian

Use for changes to `.repo-sentinel/`, `.claude/`, `.codex/`, `.agents/`, MCP configuration, or hook settings.

1. Explain why a guardrail change is needed.
2. Show the exact before/after policy diff.
3. Check that the change narrows or clarifies behavior rather than silently weakening it.
4. Require explicit user authorization before applying.
5. Run a simulated blocked command and a safe command to verify behavior.
