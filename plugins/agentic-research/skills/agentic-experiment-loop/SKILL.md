---
name: agentic-experiment-loop
description: Run a disciplined agentic experiment loop. Use when improving an AI workflow, comparing agent architectures, deciding the next probe, or promoting a new best baseline from measured evidence.
argument-hint: "[target workflow or dataset]"
---

# Agentic Experiment Loop

Use this skill for deliberate agentic-performance iteration. The goal is to improve a workflow from evidence, not to run random variants.

## Inputs

Before proposing a change, collect:

- Current baseline implementation and commit.
- Prior experiment registry or comparable run history.
- Evaluation metric definitions.
- Trace, latency, token, cost, and error data if available.
- Constraints that must remain fixed across the next experiment.

If these artifacts do not exist, create a minimal registry first with `experiment-registry`.

## Baseline Rule

Always start from the strongest valid baseline for the target task.

- If the new run wins under the accepted metric, promote it.
- If it loses or is invalid, keep the previous baseline.
- Do not branch from weaker runs just because they are newer.

## Workflow

1. Reconstruct the current best baseline.
   - Verify architecture, model/provider, prompt contract, tool usage, and score breakdown.
   - Prefer comparable scored runs over anecdotes.
2. Compare nearby variants.
   - Group same-output cohorts first when possible.
   - Separate predictive quality from operational effects such as retries, parser churn, latency, tokens, and trace shape.
3. Choose the next search direction.
   - Prefer one architectural delta at a time.
   - If progress has plateaued, define a small set of 2 to 4 bounded variants.
   - State what each variant changes and what stays fixed.
4. Apply a reproducibility gate.
   - Record intended code changes before the real run.
   - Ensure the worktree state is attributable to a commit or run tag.
   - Keep outward-facing trace names generic.
5. Run realistic smoke tests.
   - Use representative inputs.
   - Stop variants that fail determinism, schema, latency, or cost gates.
6. Launch the real experiment.
   - Capture raw output, structured metrics, trace/session IDs, model/provider, and code provenance.
7. Analyze the result.
   - Compare total score and sub-scores.
   - Inspect trace structure, tool calls, retries, errors, latency, token use, and cost.
8. Decide baseline promotion.
   - Promote only when the new run clearly beats the baseline under the target metric and preserves required quality gates.
   - Otherwise record the lesson and choose the next bounded probe.

## Design Rules

- Prefer clean, production-shaped traces over artificial activity.
- Do not add agents, tools, review phases, or retries unless evidence suggests they help.
- Treat prompt terseness, output schema size, trace topology, and model choice as first-class variables.
- Keep external identifiers neutral: `predict`, `prepare`, `review`, `decision`, or `finalize`.
- Save experiment identity in private registry artifacts, not public traces or uploads.

## Expected Output

Return:

- Current baseline summary.
- Proposed next experiment or variant set.
- Fixed variables and changed variables.
- Reproducibility gate checklist.
- Promotion criteria.
- Registry update instructions.
