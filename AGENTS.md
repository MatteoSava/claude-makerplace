# Agent Operating Guide

This repository is Claude Makerplace, a cross-agent marketplace of reusable
engineering workflows.

## Source Of Truth

- Claude Code remains the canonical plugin layout under `plugins/*`.
- Codex adapters live in `.agents/plugins/marketplace.json` and `plugins/*/.codex-plugin/plugin.json`.
- OpenCode adapters live in `opencode.json`, `.opencode/`, and the installable `opencode-plugin/` package exported by root `package.json`.
- Keep `.agents.md` as the detailed operating guide for package maintenance.

## Engineering Rules

- Use `uv` for every Python operation.
- Keep dependencies pinned and avoid new dependencies unless clearly justified.
- Prefer small patches, explicit behavior, and simple names.
- Preserve sanitization: no private names, local paths, credentials, internal hosts, run IDs, or client identifiers.
- Maintain `TODO.md` for meaningful unfinished work.

## Multi-Agent Workflow

- Keep the main agent responsible for coordination, integration, validation, and final reporting.
- Use read-only agents for broad inspection, audit, and independent validation.
- Use implementation agents only with narrow, owned write scopes.
- For bugs, reproduce with a failing test or validation before fixing.
- After package changes, run `./bin/makerplace-validate` when available and report any skipped checks.
