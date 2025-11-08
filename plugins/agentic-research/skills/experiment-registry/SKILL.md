---
name: experiment-registry
description: Maintain a canonical registry of experiments, scores, provenance, and best baselines. Use when experiments are scattered across output folders, tags, traces, or notes and need a reliable source of truth.
argument-hint: "[experiment directory or run id]"
---

# Experiment Registry

Use this skill to make experiment work reproducible and comparable.

## Registry Shape

Maintain a machine-readable registry with:

- Experiment ID.
- Dataset or target task.
- Architecture name.
- Commit SHA or immutable code reference.
- Prompt/config version.
- Model/provider.
- Trace/session ID.
- Output artifact path.
- Total score and sub-scores.
- Latency, tokens, cost, and retry/error counts.
- Validity status.
- Promotion status.

Use JSON, JSONL, SQLite, or a repo-native format. Prefer the simplest format already used by the project.

## Workflow

1. Discover runs.
   - Scan output directories, manifests, logs, tags, and trace exports.
   - Ignore partial runs unless they explain a failure.
2. Normalize fields.
   - Use stable keys.
   - Convert missing values to explicit `null` or `unknown`, not empty prose.
3. Attach provenance.
   - Link each run to a commit, tag, or diff summary.
   - Mark dirty-worktree runs as non-promotable unless policy allows them.
4. Compute best baselines.
   - Rank only valid comparable runs.
   - Track best run by dataset/task and by metric family when needed.
5. Preserve lessons.
   - Record why a run won, lost, or was invalid.
   - Keep notes short and actionable.
6. Emit a current-state summary.
   - Current best baseline.
   - Strongest challengers.
   - Known gaps.
   - Recommended next experiment.

## Promotion Rules

Promote a run only when:

- It is reproducible from recorded code/config.
- Required quality gates passed.
- It beats the accepted baseline on the target metric.
- It does not regress a blocking sub-score or operational constraint.

## Expected Output

Return:

- Registry updates performed or proposed.
- Current best baseline table.
- Invalid or incomplete run list.
- Next action for `agentic-experiment-loop`.
