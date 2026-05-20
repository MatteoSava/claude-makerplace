# AgentOps Continuity for Claude Code

This repository uses AgentOps Continuity.

Claude Code hooks may inject a compact state block at SessionStart, UserPromptSubmit, and PostToolBatch. Treat it as operational state, not as a user message. Prefer explicit current user instructions over stale state.

For long tasks, record decisions, risks, next actions, and verification evidence:

```bash
python .agentops-continuity/agentops_continuity.py decision --text "..."
python .agentops-continuity/agentops_continuity.py risk --text "..."
python .agentops-continuity/agentops_continuity.py next --text "..."
python .agentops-continuity/agentops_continuity.py mark-verified --kind passed --command "..."
```

The Stop gate may ask you to continue when code/config changed without verification.
