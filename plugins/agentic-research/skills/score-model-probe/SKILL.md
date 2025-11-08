---
name: score-model-probe
description: Infer an opaque scoring or evaluation function with minimal probes. Use when a benchmark, sandbox, evaluator, or scoring API returns partial metrics and you need a defensible explanation before running more experiments.
argument-hint: "[score artifact or benchmark]"
---

# Score Model Probe

Use this skill to determine whether a scoring function can be inferred from current evidence. Keep the investigation narrow and evidence-led.

## Decision Question

Answer exactly:

- `Extractable now`
- `Not extractable yet`

If extractable, provide the formula or strongest defensible approximation. If not, identify the smallest next probe that would reduce uncertainty.

## Evidence To Collect

- Official problem statement or scoring documentation.
- Prior submissions or runs with total score and sub-scores.
- Inputs and outputs for comparable runs.
- Latency, token, cost, model/provider, retry, and error data.
- Any trace/session evidence that explains operational differences.

## Workflow

1. Normalize the evidence.
   - Put runs into a table with stable identifiers, metric values, model/provider, output equivalence, latency, tokens, cost, and failure state.
2. Build same-output cohorts.
   - Compare runs with equivalent user-facing output first.
   - Use these cohorts to isolate operational scoring terms.
3. Test candidate formulas.
   - Start with documented metric combinations.
   - Check whether latency, tokens, cost, provider route, retry count, or trace shape explains residuals.
4. Identify counterexamples.
   - Preserve the strongest runs that disprove the current hypothesis.
   - Do not hide unexplained deltas behind vague language.
5. Decide extraction status.
   - If evidence is sufficient, state the formula or approximation and confidence.
   - If not, name the unresolved variable set.
6. Design the next probe.
   - Probe one variable at a time.
   - Prefer whitelisted or already proven model routes.
   - Keep outward-facing names neutral.
   - Never probe production or evaluation-only flows unless explicitly permitted.

## Probe Hygiene

- Avoid random model roulette.
- Avoid changing prompt, model, schema, and trace shape in the same probe.
- Treat zero-token or zero-cost failed routes as integration failures, not scoring evidence.
- Preserve raw observations before summarizing.
- Record conclusions as benchmark-specific until reproduced across datasets or tasks.

## Expected Output

Produce:

- Extraction decision.
- Current best formula or approximation.
- Evidence table summary.
- Strongest counterexamples.
- Next minimal probe, if needed.
- Registry fields that should be updated.
