---
name: python-tdd
description: Enforce strict Python test-driven development with pytest. Use when implementing Python features, fixing bugs via regression tests, writing tests first, following Red-Green-Refactor, improving test coverage, or asking for TDD with pytest. Requires a meaningful failing test before production code, minimal implementation to pass, and refactor only while tests stay green.
when_to_use: Trigger for "TDD", "red green refactor", "test first", "pytest", "add feature with tests", "fix bug with regression test", "coverage", "write tests before code", or Python behavior changes. Do not use for documentation-only edits, dependency updates, formatting-only tasks, or purely exploratory questions unless the user asks for tests.
argument-hint: "[feature, bug, or file path]"
---

# Python TDD

Implement `$ARGUMENTS` using strict Red -> Green -> Refactor. Never write or modify production code before a meaningful failing test exists.

## Bootstrap

Before editing code:

1. Check the working tree with `git status --short`. Do not overwrite user changes.
2. Identify the active test runner. Prefer project config that still uses `uv`. If uncertain, run:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/detect_pytest_command.py"
```

3. Read only the files needed for the current behavior: relevant source, existing nearby tests, `pyproject.toml`, `pytest.ini`, `tox.ini`, `noxfile.py`, and repository instructions such as `AGENTS.md` or `CLAUDE.md` when present.
4. Create a compact behavior queue. Split large requests into independently testable increments.

## Non-negotiable rules

- One observable behavior per cycle. Complete Red, Green, and Refactor for the current behavior before starting the next one.
- Red must fail for the right reason. Acceptable failures: missing symbol for new API, assertion mismatch, raised domain error, or previously reproduced bug. Do not accept failures caused only by import mistakes, syntax errors, wrong fixture wiring, or environment misconfiguration.
- Do not edit production code during Red. Test-only fixtures and helpers are allowed when needed to express behavior.
- Green means the narrow failing test passes with the smallest viable production change. No speculative features, broad abstractions, or opportunistic rewrites.
- Do not weaken, delete, or rewrite a test just to make Green pass. If the test is wrong or the requirement is inconsistent, stop and report the conflict with a proposed corrected test.
- Refactor must preserve behavior. Run tests after every refactor. If a refactor breaks tests, revert or repair before continuing.
- Prefer behavior tests over implementation tests. Verify public outcomes, contracts, side effects, and errors rather than private call sequences.
- Keep tests deterministic, isolated, and fast. Avoid real network, real time, random values without fixed seeds, and shared mutable global state.

## Workflow

### 0. Frame the behavior

For each increment, state:

- Behavior under test.
- Acceptance criteria.
- Primary test file and source file candidates.
- Narrow test command and full-suite command.

Use `TodoWrite` when available:

- `RED: <behavior>`
- `GREEN: <behavior>`
- `REFACTOR: <behavior>`

### 1. RED: write the failing pytest test

Write the smallest test that captures the desired behavior.

Python pytest defaults:

- Use function tests unless the existing project uses class-style tests.
- Use Arrange-Act-Assert structure.
- Name tests as specifications, e.g. `test_price_quote_applies_bulk_discount`.
- Use `pytest.mark.parametrize` for equivalent input/output cases.
- Use `tmp_path`, `monkeypatch`, local fakes, or `unittest.mock` to isolate filesystem, environment, clock, network, and external APIs.
- For bug fixes, first write a regression test that fails on the current bug.
- For legacy code, write characterization tests around existing behavior before refactoring.

Run the narrow test, for example:

```bash
uv run pytest -q -x tests/path/test_module.py::test_behavior_name
```

Gate: proceed only after you capture and understand the failing output.

### 2. GREEN: minimal implementation

Modify production code only enough to make the current failing test pass.

Run:

```bash
uv run pytest -q -x tests/path/test_module.py::test_behavior_name
```

Then run the relevant nearby tests. If green, run the full suite unless it is clearly too expensive; if too expensive, explain the narrower verification and the exact full command the user should run.

Gate: do not start refactoring or another behavior until the current test passes.

### 3. REFACTOR: improve safely

Refactor only after Green:

- Remove duplication.
- Improve names and boundaries.
- Simplify conditionals.
- Extract focused helpers only when duplication or complexity justifies it.
- Preserve public API unless the current behavior explicitly requires API change.

Run the narrow test and then the relevant/full suite again.

Gate: the cycle is complete only when tests are green after refactor.

## Python-specific testing policy

Use the project's existing conventions first. If there is no convention:

- Put tests under `tests/` mirroring source layout.
- Keep reusable fixtures in `conftest.py` only after they are reused by more than one test file.
- Prefer local fixtures/helpers for one-off setup.
- Prefer `pytest.approx` for floating-point assertions.
- Prefer explicit assertions over snapshot tests. Use snapshots only for stable, intentionally broad outputs.
- For async code, use the existing async test plugin. If `pytest-asyncio` is present, use `@pytest.mark.asyncio`.
- For external integrations, write unit tests around a fake boundary first; add one integration test only when the behavior depends on real framework wiring.
- For data validation, test valid case, boundary case, malformed input, and missing/None case where meaningful.
- For security- or money-sensitive paths, include branch coverage for deny/negative paths, not just happy paths.

Read [references/pytest-patterns.md](references/pytest-patterns.md) when you need concrete pytest examples. Read [references/tdd-quality-gates.md](references/tdd-quality-gates.md) when deciding whether a cycle is valid.

## Coverage and mutation-thinking

Coverage is a guide, not the objective.

- Aim for at least 80% line coverage for normal modules when coverage exists in the project.
- Critical paths such as auth, payments, authorization, data validation, migrations, and irreversible side effects need branch-level tests for success and failure paths.
- When a test passes too easily, perform mutation-thinking: identify the smallest wrong implementation that would still pass. If a plausible wrong implementation passes, strengthen the test before moving on.
- Run mutation tools only if already configured, such as `mutmut` or `cosmic-ray`; do not install new tools without being asked.

## Output format

For every cycle, report:

```text
Behavior: <one observable behavior>
RED: <test path>::<test name>
RED result: <command + key failing line>
GREEN changes: <production files changed>
GREEN result: <command + pass/fail>
REFACTOR: <changes or "none needed">
FINAL verification: <command + result>
Next: <next behavior or done>
```

Keep explanations concise. Include exact commands and file paths so the user can reproduce the state.

## Optional stricter mode

For high-risk changes or when the user says "strict", pause after Red and show the failing test plus failure output before Green. Continue only after the user accepts the test or the requirement is unambiguous from existing specs.

## Common failure handling

- Red unexpectedly passes: the test is not proving new behavior. Strengthen the test or choose a smaller behavior.
- Red fails for setup/import reasons: fix test setup only, then rerun Red. Do not touch production behavior yet.
- Green requires large design work: stop, split the behavior smaller, and complete the smallest valid slice first.
- Full suite has unrelated failures: report them separately, keep current cycle evidence, and avoid modifying unrelated code unless requested.
- Existing tests conflict with new behavior: report the conflict with file paths and ask for the intended contract only if the repository does not make it clear.
