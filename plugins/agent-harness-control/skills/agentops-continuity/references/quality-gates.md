# Quality gates

AgentOps quality gates are conservative by default.

## Stop gate

The Stop gate blocks final response when:

- active task exists
- verification is required
- verification status is not accepted

Accepted statuses are configurable in `policy.json`:

- `passed`
- `not-applicable`
- `skipped-with-reason`
- `manual-review`

## Auto verification detection

`PostToolUse` marks verification as passed after successful commands matching configured regexes, such as:

- `pytest`
- `python -m pytest`
- `npm test`
- `pnpm test`
- `go test`
- `cargo test`
- `ruff check`
- `mypy`
- `terraform plan`

Commands containing `|| true`, `; true`, `--help`, or `--version` are ignored by default.

## Change tracking

File writes and patches mark touched files. Source/config/IaC/package files mark the task as requiring verification.
