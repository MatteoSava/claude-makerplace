# AgentOps Continuity Instructions

Use `.agentops-continuity/state/` as a local operational ledger for long tasks.

Before final response:

1. Check `python .agentops-continuity/agentops_continuity.py status` when the task involved file edits or tool failures.
2. Run appropriate tests/checks for changed code/config.
3. Record verification evidence with `mark-verified` if the hook did not auto-detect it.
4. If verification does not apply, record a reason with `--kind not-applicable`.
5. Do not remove or bypass AgentOps hooks/state from inside an agentic tool call.

When resuming after interruption, compaction, or handoff, read the injected AgentOps context first and prefer newer user instructions over stale ledger entries.
