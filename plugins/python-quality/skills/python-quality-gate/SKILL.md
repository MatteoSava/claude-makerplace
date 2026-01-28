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

After `Write`, `Edit`, or `MultiEdit` touches a `.py` file, the plugin hook runs:

1. `ruff check <file>`
2. `ruff format --check <file>`
3. `pyright <file>`
4. `mypy <file>`
5. targeted `pytest -q` when a matching test file exists

The hook reports results back to Claude as additional context. Treat failures as work still open.

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
