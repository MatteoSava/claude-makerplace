# Install and operations

## Minimal Claude install

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/install.py" --target . --claude
cat .claude/settings.repo-sentinel.example.json
```

Merge the hooks into `.claude/settings.json`, then review with `/hooks`.

## Minimal Codex install

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/install.py" --target . --codex
codex execpolicy check --pretty --rules .codex/rules/repo-sentinel.rules -- git reset --hard
```

Trust the project `.codex/` layer if Codex prompts you.

## Dual install

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/install.py" --target . --claude --codex --append-agents --append-claude
```

## Validate the core script

```bash
uv run python .repo-sentinel/repo_sentinel.py status
uv run python .repo-sentinel/repo_sentinel.py check --record
```

## Simulate a Claude/Codex PreToolUse event

```bash
printf '{"hook_event_name":"PreToolUse","cwd":"%s","tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' "$PWD" \
  | uv run python .repo-sentinel/repo_sentinel.py hook
```

Expected: JSON denial.
