---
name: benchmark-run-operations
description: Launch, monitor, upload, and compare benchmark or sandbox runs with reproducible provenance. Use when managing scored AI runs, training-only submissions, run health, score recording, or post-run insight reports.
argument-hint: "[run id or benchmark target]"
---

# Benchmark Run Operations

Use this skill for operational handling of benchmark runs after the experiment design is clear.

## Run Gate

Before a real externally scored run:

- Commit intended code changes or record an immutable code reference.
- Require a clean worktree unless the user explicitly accepts a dirty run.
- Save runtime configuration, model/provider, prompt/config version, and run tag.
- Keep public trace, upload, and file names neutral.
- Confirm the actual runtime mode is not a dry run, fallback, or mock path.

## Launch Workflow

1. Create a new run folder or registry row using the repository's helper script.
2. Start long-running work in a terminal multiplexer.
3. Save:
   - run ID
   - process/session name
   - log path
   - trace/session IDs
   - git identity
   - dataset or target task
4. Watch for meaningful state changes instead of busy polling.
5. Report only completed dataset, stopped, failed, or fully completed states.

## Upload Workflow

Use only for training, sandbox, or explicitly non-production uploads unless the user authorizes another target.

- Verify the target page/API section before uploading.
- Never upload to evaluation/production controls by accident.
- Never upload source code when only result artifacts are expected.
- Use neutral filenames.
- Verify trace/session visibility before submitting IDs.
- Record returned scores and sub-scores in experiment metadata.

## Compare Workflow

When a run has failed cases, unexpected score movement, missing artifacts, unusual cost, or unusual latency:

1. Compare against the current baseline and nearest variants.
2. Prefer registry-backed metrics.
3. Include score deltas, failed cases, latency, cost, tokens, and trace status.
4. Use final observability data over early local sidecars when they disagree.
5. Save the insight report in the run metadata.

## Expected Output

Return:

- Run status and provenance.
- Runtime mode.
- Upload status and saved score fields.
- Comparison summary.
- Registry refresh required or completed.
