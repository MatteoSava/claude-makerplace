# Claude Makerplace

> A cross-agent marketplace of reusable engineering workflows — packaged as Claude Code plugins, with first-class **Codex** and **OpenCode** adapters over the same source layout.

The marketplace contains 24 skills across 7 plugins, plus 4 slash commands, 3 Claude Code subagents, and 3 runtime hooks — with Codex and OpenCode adapters layered on the same source.

---

## Table of Contents

- [Why Makerplace](#why-makerplace)
- [The Autoresearch Loop](#the-autoresearch-loop)
- [Plugins](#plugins)
- [Install](#install)
  - [Claude Code](#claude-code)
  - [Codex](#codex)
  - [OpenCode](#opencode)
- [Hook Profiles](#hook-profiles)
- [Feedback Delivery](#feedback-delivery)
- [CI / Validation](#ci--validation)
- [Repository Layout](#repository-layout)

---

## Why Makerplace

Most agent workflows live as ad-hoc prompts. Makerplace turns them into **versioned, testable, sanitized plugins** that work across Claude Code, Codex, and OpenCode from a single source of truth under `plugins/*`.

The core idea: **skills are not static instructions**. When a skill produces a wrong result, the agent updates the skill itself so the mistake doesn't repeat.

## The Autoresearch Loop

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

Encoded across the `skill-autoresearch-loop` skill, the `skill-curator` agent, and the `/skill-evolve` command. When a user corrects a mistake or reports friction, the system doesn't just fix the immediate answer — it patches the underlying skill so every future invocation benefits.

For scored experiments, a parallel loop applies:

```
baseline → bounded variant → reproducible run → score/trace review → promote or discard
```

---

## Plugins

### 🧪 `agentic-research`

Self-improving agent workflows and experiment infrastructure.

| Skill | Purpose |
|---|---|
| `skill-autoresearch-loop` | Turn feedback, missed behavior, and repeated fixes into durable skill improvements |
| `agentic-experiment-loop` | Disciplined A/B iteration: baseline → variant → measured run → promote or discard |
| `benchmark-run-operations` | Launch, monitor, upload, and compare scored benchmark runs with safety gates |
| `experiment-registry` | Machine-readable registry of experiment runs with provenance, scores, and promotion state |
| `score-model-probe` | Reverse-engineer opaque scoring functions with minimal targeted probes |

### ☁️ `cloud-delivery`

Cloud deployment, Azure DevOps delivery, and operational workflows.

| Skill | Purpose |
|---|---|
| `azure-container-app-deploy` | Azure Container Apps deployment lifecycle and quick diagnosis |
| `template-pipeline-authoring` | Generate Azure DevOps YAML pipelines from internal template catalogs |
| `azure-devops-pr-workflow` | Create and update Azure DevOps PRs via MCP with proper repo/branch resolution |
| `work-item-linking` | Azure DevOps work item discovery and PR linking via `AB#` references |
| `authentication-troubleshooting` | Debug browser → API → cloud auth chains: token decode, issuer/audience, managed identity |
| `internal-wiki-query` | Query organization knowledge bases through MCP, preserving citations |
| `trmnl-terminus-ops` | Self-hosted TRMNL/Terminus e-ink device operations: health checks, repair, screen publishing |

### 🎨 `product-engineering`

Full-stack product work: frontend, streaming, UI validation, and Telegram integrations.

| Skill | Purpose |
|---|---|
| `react-typescript-standards` | React + TypeScript standards: explicit types, reducer state, streaming UI, accessibility |
| `sse-chat-streaming` | SSE chat streaming with explicit event protocol and frontend AbortController parsing |
| `playwright-ui-validation` | Browser-level UI validation: chat flows, streaming, theme toggle, mobile viewport |
| `webqa-devtools` | Browser QA and debugging workflow using Chrome DevTools MCP evidence |
| `telegram-miniapp-feature` | Full-stack Telegram Mini App features with `initData` HMAC validation |
| `ton-wallet-integration` | TON Connect wallet and on-chain payment flows in Telegram Mini Apps |
| `intent-system-extension` | Add intents to deterministic AI behavior systems: type registry, scoring, cooldowns |

### 📚 `repository-documentation`

Source-grounded repository documentation workflows.

| Skill | Purpose |
|---|---|
| `repo-docs-wiki` | Build, ingest, query, lint, and repair source-grounded `docs/` wikis and LLM-readable indexes |

> **Hook:** Runs on Stop after docs-wiki files change. Refreshes the docs index when safe, then runs deterministic docs-wiki lint and health checks.

### 🐍 `python-quality`

Python quality automation and test-driven development using `uv` with pinned tooling.

| Skill | Purpose |
|---|---|
| `python-quality-gate` | Quality gates for Python edits: Ruff → Pyright → Mypy → pytest, all via `uv` |
| `python-tdd` | Strict Red → Green → Refactor workflow for Python features and bug fixes with pytest |

> **Agent:** `python-quality-reviewer` — delegated uv-only Python review focused on lint, type checking, and test coverage.
>
> **Hooks:** Per-file checks after every `.py` edit; broader project checks on Stop.
>
> **Pinned tooling:** `ruff==0.15.8` · `pyright==1.1.409` · `mypy==2.0.0` · `pytest==9.0.3`

### 🛡️ `agent-harness-control`

Agent runtime guardrails, hook scaffolds, continuity ledgers, execpolicy rules, and repository control-plane workflows.

| Skill | Purpose |
|---|---|
| `repo-sentinel` | Install and operate deterministic repository guardrails for Claude Code and Codex hooks |
| `agentops-continuity` | Maintain local task state, compaction recovery, handoff, and verification continuity |

### ⚙️ `makerplace-system`

Marketplace maintenance, audit, and self-improvement infrastructure.

**Commands**

| Command | Purpose |
|---|---|
| `/marketplace-health` | Audit marketplace readiness, sanitization, hook health, and validation drift |
| `/skill-evolve` | Turn feedback or repeated friction into a generalized skill improvement |
| `/release-readiness` | Prepare a release review with validation evidence and limitations |
| `/feedback-makerplace` | Collect sanitized plugin feedback and send it through a configured webhook |

**Agents**

| Agent | Purpose |
|---|---|
| `marketplace-auditor` | Read-only review for packaging, sanitization, provenance, and validation coverage |
| `skill-curator` | Targeted improvement of impacted skills after feedback, using the autoresearch loop |

> **Hook:** `makerplace-guard.sh` — scans edited plugin artifacts for leak markers (local paths, internal hosts, credentials, IPs).

---

## Install

### Claude Code

```bash
/plugin marketplace add ./claude-makerplace
/plugin install agentic-research@claude-makerplace
/plugin install cloud-delivery@claude-makerplace
/plugin install product-engineering@claude-makerplace
/plugin install repository-documentation@claude-makerplace
/plugin install python-quality@claude-makerplace
/plugin install agent-harness-control@claude-makerplace
/plugin install makerplace-system@claude-makerplace
/reload-plugins
```

Invoke a skill:

```
/agentic-research:agentic-experiment-loop
/repository-documentation:repo-docs-wiki
/product-engineering:webqa-devtools
/python-quality:python-quality-gate
/agent-harness-control:repo-sentinel
/makerplace-system:marketplace-health
```

### Codex

Use this repository as a local Codex marketplace:

```text
.agents/plugins/marketplace.json
```

It exposes the same organized plugin names as Claude Code. Per-plugin Codex manifests live at `plugins/*/.codex-plugin/plugin.json`.

Enable plugin hooks in `.codex/config.toml`:

```toml
[features]
hooks = true
plugin_hooks = true
```

Codex runs plugin-local hooks from each plugin's `hooks/hooks.json` when plugin hooks are enabled and trusted. For project-local hooks, use `.codex/hooks.json`.

### OpenCode

Run OpenCode from the repository root to load `opencode.json` and the `.opencode/` directory automatically.

From another working directory, point OpenCode at both:

```bash
OPENCODE_CONFIG=/path/to/claude-makerplace/opencode.json \
OPENCODE_CONFIG_DIR=/path/to/claude-makerplace/.opencode \
opencode
```

For an installable plugin config:

```json
{
  "plugin": ["file:///path/to/claude-makerplace/opencode-plugin/index.js"]
}
```

Once published to npm:

```bash
opencode plugin @claude-makerplace/opencode-plugin
```

To enable Chrome DevTools MCP for `webqa-devtools`, pass tuple options:

```json
{
  "plugin": [
    ["@claude-makerplace/opencode-plugin", { "enableChromeDevtoolsMcp": true }]
  ]
}
```

The default OpenCode primary agent is `makerplace-lead`. See `docs/opencode-install.md` for package behavior, local install options, and OpenCode hook limitations.

---

## Hook Profiles

Control Python quality gate strictness with `MAKERPLACE_HOOK_PROFILE`:

| Profile | Checks |
|---|---|
| `minimal` | Ruff lint + format |
| `standard` | Ruff + Pyright + Mypy + targeted pytest |
| `strict` | All standard checks + full test suite |

Set `MAKERPLACE_HOOKS=off` to disable hooks temporarily.

---

## Feedback Delivery

`/feedback-makerplace` collects sanitized session feedback. Delivery is configured through environment variables.

<details>
<summary><strong>Generic webhook</strong></summary>

```bash
export MAKERPLACE_FEEDBACK_DESTINATION=webhook
export MAKERPLACE_FEEDBACK_WEBHOOK_URL="https://example.com/feedback"
```

</details>

<details>
<summary><strong>GitHub issue</strong></summary>

```bash
export MAKERPLACE_FEEDBACK_DESTINATION=github
export MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY="owner/repo"
export MAKERPLACE_FEEDBACK_GITHUB_TOKEN="<token-with-issues-write>"
export MAKERPLACE_FEEDBACK_GITHUB_LABELS="feedback,plugin"
```

</details>

<details>
<summary><strong>GitHub issue comment</strong></summary>

```bash
export MAKERPLACE_FEEDBACK_DESTINATION=github
export MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY="owner/repo"
export MAKERPLACE_FEEDBACK_GITHUB_ISSUE_NUMBER="123"
export MAKERPLACE_FEEDBACK_GITHUB_TOKEN="<token-with-issues-write>"
```

</details>

Set `MAKERPLACE_FEEDBACK_DESTINATION=auto` to use GitHub when `MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY` is set, otherwise fall back to `MAKERPLACE_FEEDBACK_WEBHOOK_URL`.

---

## CI / Validation

GitHub Actions runs on push, PR, and manual dispatch with pinned infrastructure:

```yaml
actions/checkout@v6.0.2
astral-sh/setup-uv@v8.1.0
uv: 0.11.11
python: 3.12.13
```

CI and local validation share a single entrypoint:

```bash
./bin/makerplace-validate
```

This checks JSON validity, Claude and Codex plugin manifest conventions, OpenCode adapter links, skill frontmatter, README consistency, selection map coverage, hook scripts, executable permissions, privacy leak markers, Claude plugin validation (when available), Python and repo-docs hook smoke tests, and feedback sender behavior.

---

## Repository Layout

```
claude-makerplace/
├── .claude-plugin/marketplace.json      # Claude Code marketplace
├── .agents/plugins/marketplace.json     # Codex marketplace
├── .opencode/                           # OpenCode project adapter
├── opencode-plugin/                     # Installable OpenCode package
├── opencode.json
├── package.json
├── bin/makerplace-validate              # Canonical validation entrypoint
├── .github/workflows/validate.yml
├── docs/
└── plugins/
    ├── agentic-research/         (5 skills)
    ├── cloud-delivery/           (7 skills)
    ├── product-engineering/      (7 skills)
    ├── repository-documentation/ (1 skill, 1 hook)
    ├── python-quality/           (2 skills, 1 agent, 1 hook)
    ├── agent-harness-control/    (2 skills)
    └── makerplace-system/        (4 commands, 2 agents, 1 hook)
```

**Source of truth:** Claude Code remains the canonical plugin layout under `plugins/*`. Codex and OpenCode are thin adapters over the same source.

- **Claude Code:** `.claude-plugin/marketplace.json` + `plugins/*/.claude-plugin/plugin.json`
- **Codex:** `.agents/plugins/marketplace.json` + `plugins/*/.codex-plugin/plugin.json`
- **OpenCode:** `opencode.json` + `.opencode/` + `opencode-plugin/` (published as `@claude-makerplace/opencode-plugin`)

---

## License

See [`LICENSE`](./LICENSE).
