# Threat model

Repo Sentinel is a local deterministic guardrail, not a sandbox boundary.

## Protects against

- Accidental destructive shell commands.
- Agent writes to known sensitive/generated/config paths.
- Silent modification of agent settings and hook configuration.
- Common secret patterns introduced by generated code.
- Agents ending tasks after code changes without running checks.

## Does not fully protect against

- A malicious user with shell access editing or deleting the hook files.
- Every possible shell obfuscation, especially complex scripts, shell expansions, aliases, or interpreter one-liners.
- All secret formats.
- Commands run outside Claude Code/Codex.
- MCP tools whose arguments do not expose paths or commands in predictable fields.

## Defense in depth

Recommended complements:

- Git pre-commit hooks.
- CI-required checks.
- Secret scanners such as gitleaks/trufflehog.
- Least-privilege sandbox/approval modes.
- Read-only or isolated worktrees for untrusted tasks.
- Codex execpolicy rules and Claude managed policy hooks for enterprise environments.
