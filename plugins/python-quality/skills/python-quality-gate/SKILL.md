---
name: python-quality-gate
description: Maintain Python edit quality gates using uv, Ruff, Pyright, Mypy, and targeted pytest. Use when editing Python code, configuring hooks, explaining Python validation failures, or updating quality tooling without npm/npx.
argument-hint: "[python file or failure output]"
---

# Python Quality Gate

Use this skill when Python files are edited or when the plugin's Python hook reports failures.

## Tooling Contract

- Use `uv` for every Python operation.
- Do not use `pip`, system Python, npm, or npx.
- Keep tool versions pinned.
- Prefer project configuration from `pyproject.toml`, `mypy.ini`, `pyrightconfig.json`, and `uv.lock`.

Pinned hook tools:

- `ruff==0.15.8`
- `pyright==1.1.409`
- `mypy==2.0.0`
- `pytest==9.0.3`

## Automatic Hook Behavior

After `Write`, `Edit`, or `MultiEdit` touches a `.py` file, the PostToolUse hook runs light per-file checks:

1. `ruff check <file>`
2. `ruff format --check <file>`
3. `pyright <file>`
4. `mypy <file>`

Before Claude returns to the user, the Stop hook runs broader project checks:

1. `ruff check .`
2. `ruff format --check .`
3. `pyright` over discovered Python files
4. `mypy` over discovered Python files
5. `pytest -q` for the test suite when tests exist

The PostToolUse hook reports results back to Claude as additional context. The Stop hook is silent when checks pass and blocks stopping when checks fail. Treat hook failures as work still open.

## Fix Order

1. Fix syntax or import errors first.
2. Run Ruff formatting or adjust formatting manually.
3. Fix Ruff lint findings.
4. Fix Pyright type errors.
5. Fix Mypy type errors.
6. Fix targeted tests.

Prefer the smallest code change that resolves the failure. Do not disable rules unless the codebase already uses that pattern or the rule is demonstrably wrong for the case.

## Expected Output

When reporting Python quality status, include:

- file checked
- commands that failed
- concise cause
- fix applied
- remaining failures, if any
