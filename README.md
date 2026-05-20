# Claude Makerplace

A Claude Code plugin marketplace that packages reusable agent workflows into organized, installable plugins, with thin Codex and OpenCode adapters over the same source layout.

## How Autoresearch Works

The core idea behind this project: skills are not static instructions. When a skill produces a wrong result, the agent updates the skill itself so the mistake doesn't repeat.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Skill Autoresearch Loop                      │
│                                                                 │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐     │
│   │  Use     │    │  Observe     │    │  Identify         │     │
│   │  Skill   │───▶│  Failure or  │───▶│  Impacted         │     │
│   │          │    │  Friction    │    │  SKILL.md / Hook  │     │
│   └──────────┘    └──────────────┘    └─────────┬─────────┘     │
│                                                 │               │
│                                                 ▼               │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐     │
│   │  Reuse   │    │  Validate    │    │  Generalize       │     │
│   │  Better  │◀───│  Package     │◀───│  The Fix          │     │
│   │  Behavior│    │  Integrity   │    │  (not hardcode)   │     │
│   └──────────┘    └──────────────┘    └───────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

This loop is encoded across the `skill-autoresearch-loop` skill, the `skill-curator` agent, and the `/skill-evolve` command. When a user corrects a mistake or reports friction, the system doesn't just fix the immediate answer — it patches the underlying skill so every future invocation benefits.

For benchmark and experiment workflows, a parallel loop applies:

```
baseline → bounded variant → reproducible run → score/trace review → promote or discard
```

## Plugins

The marketplace contains 23 skills across 6 plugins, plus 4 slash commands, 3 Claude Code subagents, 4 OpenCode adapter agents, and 3 runtime hooks.

### agentic-research

Self-improving agent workflows and experiment infrastructure.

| Skill | Purpose |
|-------|---------|
| `skill-autoresearch-loop` | Turn feedback, missed behavior, and repeated fixes into durable skill improvements |
| `agentic-experiment-loop` | Disciplined A/B experiment iteration: baseline → variant → measured run → promote or discard |
| `benchmark-run-operations` | Launch, monitor, upload, and compare scored benchmark runs with safety gates |
| `experiment-registry` | Machine-readable registry of experiment runs with provenance, scores, and promotion state |
| `score-model-probe` | Reverse-engineer opaque scoring functions with minimal targeted probes |
| `azure-ai-sdk-research` | Research-first Azure AI SDK investigation (Foundry, AI.Projects, Responses API) |
| `azure-ai-trace-continuity` | Diagnose fragmented OpenTelemetry traces across Azure AI Foundry and Application Insights |

### cloud-delivery

Cloud deployment, Azure DevOps delivery, and operational workflows.

| Skill | Purpose |
|-------|---------|
| `azure-container-app-deploy` | Azure Container Apps deployment lifecycle and quick diagnosis |
| `template-pipeline-authoring` | Generate Azure DevOps YAML pipelines from internal template catalogs |
| `azure-devops-pr-workflow` | Create and update Azure DevOps PRs via MCP with proper repo/branch resolution |
| `work-item-linking` | Azure DevOps work item discovery and PR linking via `AB#` references |
| `authentication-troubleshooting` | Debug browser → API → cloud auth chains: token decode, issuer/audience, managed identity |
| `internal-wiki-query` | Query organization knowledge bases through MCP, preserving citations |
| `trmnl-terminus-ops` | Self-hosted TRMNL/Terminus e-ink device operations: health checks, repair, screen publishing |

### product-engineering

Full-stack product work: frontend, streaming, UI validation, and Telegram integrations.

| Skill | Purpose |
|-------|---------|
| `react-typescript-standards` | React + TypeScript standards: explicit types, reducer state, streaming UI, accessibility |
| `sse-chat-streaming` | SSE chat streaming with explicit event protocol and frontend AbortController parsing |
| `playwright-ui-validation` | Browser-level UI validation: chat flows, streaming, theme toggle, mobile viewport |
| `telegram-miniapp-feature` | Full-stack Telegram Mini App features with `initData` HMAC validation |
| `ton-wallet-integration` | TON Connect wallet and on-chain payment flows in Telegram Mini Apps |
| `intent-system-extension` | Add intents to deterministic AI behavior systems: type registry, scoring, cooldowns |

### repository-documentation

Source-grounded repository documentation workflows.

| Skill | Purpose |
|-------|---------|
| `repo-docs-wiki` | Build, ingest, query, lint, and repair source-grounded docs/ wikis and LLM-readable indexes |

**Hook:** Runs on Stop after docs-wiki files change. It refreshes the docs index when safe, then runs deterministic docs-wiki lint and health checks. Broad repo mapping and subagent fleets remain explicit skill workflows, not hook-triggered background work.

### python-quality

Python quality automation and test-driven development using `uv` with pinned tooling.

| Skill | Purpose |
|-------|---------|
| `python-quality-gate` | Quality gates for Python edits: Ruff → Pyright → Mypy → pytest, all via `uv` |
| `python-tdd` | Strict Red → Green → Refactor workflow for Python features and bug fixes with pytest |

**Agent:** `python-quality-reviewer` — delegated uv-only Python review focused on lint, type checking, and test coverage.

**Hooks:** Runs light per-file checks after every `.py` edit, then runs broader project checks on Stop before Claude returns to the user. Tooling is pinned:
`ruff==0.15.8` · `pyright==1.1.409` · `mypy==2.0.0` · `pytest==9.0.3`

### makerplace-system

Marketplace maintenance, audit, and self-improvement infrastructure.

**Commands:**

- `/marketplace-health` — audit marketplace readiness, sanitization, hook health, and validation drift
- `/skill-evolve` — turn feedback or repeated friction into a generalized skill improvement
- `/release-readiness` — prepare a release review with validation evidence and limitations
- `/feedback-makerplace` — collect sanitized plugin feedback and send it through a configured webhook

**Agents:**

- `marketplace-auditor` — read-only review for packaging, sanitization, provenance, and validation coverage
- `skill-curator` — targeted improvement of impacted skills after feedback, using the autoresearch loop

**Hook:** `makerplace-guard.sh` — scans edited plugin artifacts for leak markers (local paths, internal hosts, credentials, IPs).

## Hook Profiles

Control the Python quality gate strictness with `MAKERPLACE_HOOK_PROFILE`:

| Profile | Checks |
|---------|--------|
| `minimal` | Ruff lint + format |
| `standard` | Ruff + Pyright + Mypy + targeted pytest |
| `strict` | All standard checks + full test suite |

Set `MAKERPLACE_HOOKS=off` to disable hooks temporarily.

## Cross-Agent Surfaces

Claude Code is the canonical package format:

- marketplace: `.claude-plugin/marketplace.json`
- plugin manifests: `plugins/*/.claude-plugin/plugin.json`
- source components: plugin-local `skills/`, `commands/`, `agents/`, `hooks/`, and `scripts/`

Codex uses a parallel marketplace and per-plugin manifests:

- marketplace: `.agents/plugins/marketplace.json`
- plugin manifests: `plugins/*/.codex-plugin/plugin.json`
- plugin hooks: `plugins/*/hooks/hooks.json` command hooks can run when Codex plugin hooks are enabled and trusted
- project hooks: `.codex/hooks.json` can register project-local command hooks; enable them through `.codex/config.toml`

OpenCode uses a project-local adapter:

- config: `opencode.json`
- runtime plugin: `.opencode/plugins/claude-makerplace.js`
- skills and commands: `.opencode/skills` and `.opencode/commands` link to the Claude plugin source files
- agents: `.opencode/agents` provides OpenCode-native versions of the lead, auditor, curator, and Python quality roles

## Feedback Delivery

`/feedback-makerplace` collects sanitized session feedback. Delivery is configured through environment variables.

Generic webhook:

```bash
export MAKERPLACE_FEEDBACK_DESTINATION=webhook
export MAKERPLACE_FEEDBACK_WEBHOOK_URL="https://example.com/feedback"
```

GitHub issue:

```bash
export MAKERPLACE_FEEDBACK_DESTINATION=github
export MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY="owner/repo"
export MAKERPLACE_FEEDBACK_GITHUB_TOKEN="<token-with-issues-write>"
export MAKERPLACE_FEEDBACK_GITHUB_LABELS="feedback,plugin"
```

GitHub issue comment:

```bash
export MAKERPLACE_FEEDBACK_DESTINATION=github
export MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY="owner/repo"
export MAKERPLACE_FEEDBACK_GITHUB_ISSUE_NUMBER="123"
export MAKERPLACE_FEEDBACK_GITHUB_TOKEN="<token-with-issues-write>"
```

`MAKERPLACE_FEEDBACK_DESTINATION=auto` uses GitHub when `MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY` is set, otherwise it uses `MAKERPLACE_FEEDBACK_WEBHOOK_URL`.

## CI/CD

GitHub Actions validation runs on push, PR, and manual dispatch with pinned infrastructure:

```yaml
actions/checkout@v6.0.2
astral-sh/setup-uv@v8.1.0
uv: 0.11.11
python: 3.12.13
```

The CI workflow and local validation use the same entrypoint:

```bash
./bin/makerplace-validate
```

This checks: JSON validity, Claude and Codex plugin manifest conventions, OpenCode adapter links, skill frontmatter, README consistency, selection map coverage, hook scripts, executable permissions, privacy leak markers, Claude plugin validation (when available), Python and repo-docs hook smoke tests, and feedback sender behavior.

## Install

### Claude Code

```
/plugin marketplace add ./claude-makerplace
/plugin install agentic-research@claude-makerplace
/plugin install cloud-delivery@claude-makerplace
/plugin install product-engineering@claude-makerplace
/plugin install repository-documentation@claude-makerplace
/plugin install python-quality@claude-makerplace
/plugin install makerplace-system@claude-makerplace
/reload-plugins
```

Invoke skills:

```
/agentic-research:agentic-experiment-loop
/repository-documentation:repo-docs-wiki
/python-quality:python-quality-gate
/python-quality:python-tdd
/makerplace-system:marketplace-health
/makerplace-system:feedback-makerplace
```

### Codex

Use this repository as a local Codex marketplace. The marketplace file is:

```text
.agents/plugins/marketplace.json
```

It exposes the same organized plugin names:

```text
agentic-research
cloud-delivery
product-engineering
repository-documentation
python-quality
makerplace-system
```

Codex can run marketplace plugin hooks from each plugin's `hooks/hooks.json` when plugin hooks are enabled and the hook command is trusted. For project-local hooks, use `.codex/hooks.json` plus:

```toml
[features]
hooks = true
plugin_hooks = true
```

### OpenCode

Run OpenCode from the repository root to load the project config and `.opencode`
directory automatically. To load the package from another working directory,
point OpenCode at both the config file and adapter directory:

```bash
OPENCODE_CONFIG=/path/to/claude-makerplace/opencode.json \
OPENCODE_CONFIG_DIR=/path/to/claude-makerplace/.opencode \
opencode
```

The default OpenCode primary agent is `makerplace-lead`. OpenCode also sees the
project skills, commands, and subagents through `.opencode/`.

## Project Structure

```
claude-makerplace/
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
├── .opencode/
├── opencode.json
├── .github/workflows/validate.yml
├── bin/makerplace-validate
├── docs/
└── plugins/
    ├── agentic-research/   (7 skills)
    ├── cloud-delivery/     (7 skills)
    ├── product-engineering/ (6 skills)
    ├── repository-documentation/ (1 skill)
    ├── python-quality/     (2 skills, 1 agent, 1 hook)
    └── makerplace-system/  (4 commands, 2 agents, 1 hook)
```
