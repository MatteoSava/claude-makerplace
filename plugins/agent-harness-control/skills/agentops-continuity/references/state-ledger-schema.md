# State ledger schema

## `current-task.json`

```json
{
  "id": "task-abc12345",
  "objective": "...",
  "status": "active|verified|done|abandoned",
  "verification_required": true,
  "verification": {
    "status": "unknown|passed|failed|not-applicable|skipped-with-reason|manual-review",
    "command": "pytest -q",
    "note": "...",
    "source": "cli|PostToolUse|PostToolUseFailure",
    "updated_at": "..."
  },
  "touched_files": ["src/example.py"],
  "constraints": [],
  "next_actions": [],
  "stop_block_count": 0
}
```

## Markdown ledgers

- `session-ledger.md` is append-only.
- `decisions.md` is append-only unless a human intentionally edits it.
- `open-risks.md` may be manually pruned when risks are closed, but closure should be recorded.
- `context-essentials.md` is curated and may be rewritten by a curator agent.

## JSONL streams

- `compact-summaries.jsonl`
- `hook-events.jsonl`
- `prompts.jsonl`
- `tool-batches.jsonl`
- `blocked-tools.jsonl`
- `errors.jsonl`

These are operational logs, not stable APIs.
