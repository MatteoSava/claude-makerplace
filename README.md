# Claude Makerplace

A Claude Code plugin marketplace that packages reusable agent workflows into organized, installable plugins — with skills that improve themselves from real usage.

## How Autoresearch Works

The core idea behind this project: skills are not static instructions. When a skill produces a wrong result, the agent updates the skill itself so the mistake doesn't repeat.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Skill Autoresearch Loop                       │
│                                                                 │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐     │
│   │  Use      │    │  Observe     │    │  Identify         │     │
│   │  Skill    │───▶│  Failure or  │───▶│  Impacted         │     │
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

The marketplace contains 23 skills across 5 plugins, plus 3 slash commands, 3 subagents, and 2 runtime hooks.

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

Cloud deployment, Azure DevOps delivery, and infrastructure standards.

| Skill | Purpose |
|-------|---------|
| `azure-container-app-deploy` | Azure Container Apps deployment lifecycle and quick diagnosis |
| `bicep-infrastructure-standards` | Azure Bicep IaC: small modules, managed identity, narrow RBAC, Key Vault references |
| `template-pipeline-authoring` | Generate Azure DevOps YAML pipelines from internal template catalogs |
| `azure-devops-pr-workflow` | Create and update Azure DevOps PRs via MCP with proper repo/branch resolution |
| `work-item-linking` | Azure DevOps work item discovery and PR linking via `AB#` references |
| `authentication-troubleshooting` | Debug browser → API → cloud auth chains: token decode, issuer/audience, managed identity |
| `internal-wiki-query` | Query organization knowledge bases through MCP, preserving citations |
| `aspnet-api-standards` | Clean ASP.NET Core Minimal API patterns with RFC 7807 errors and JWT auth |
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

### python-quality

Python quality automation using `uv` with pinned tooling.

| Skill | Purpose |
|-------|---------|
| `python-quality-gate` | Quality gates for Python edits: Ruff → Pyright → Mypy → pytest, all via `uv` |

**Agent:** `python-quality-reviewer` — delegated uv-only Python review focused on lint, type checking, and test coverage.

**Hook:** Runs automatically after every `.py` file edit with pinned versions:
`ruff==0.15.8` · `pyright==1.1.409` · `mypy==2.0.0` · `pytest==9.0.3`

### makerplace-system

Marketplace maintenance, audit, and self-improvement infrastructure.

**Commands:**
- `/marketplace-health` — audit marketplace readiness, sanitization, hook health, and validation drift
- `/skill-evolve` — turn feedback or repeated friction into a generalized skill improvement
- `/release-readiness` — prepare a release review with validation evidence and limitations

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

This checks: JSON validity, plugin manifest conventions, skill frontmatter, README consistency, selection map coverage, hook scripts, executable permissions, privacy leak markers, Claude plugin validation (when available), and a Python hook smoke test.

## Install

```
/plugin marketplace add ./claude-makerplace
/plugin install agentic-research@claude-makerplace
/plugin install cloud-delivery@claude-makerplace
/plugin install product-engineering@claude-makerplace
/plugin install python-quality@claude-makerplace
/plugin install makerplace-system@claude-makerplace
/reload-plugins
```

Invoke skills:

```
/agentic-research:agentic-experiment-loop
/python-quality:python-quality-gate
/makerplace-system:marketplace-health
```

## Project Structure

```
claude-makerplace/
├── .claude-plugin/marketplace.json
├── .github/workflows/validate.yml
├── bin/makerplace-validate
└── plugins/
    ├── agentic-research/   (7 skills)
    ├── cloud-delivery/     (9 skills)
    ├── product-engineering/ (6 skills)
    ├── python-quality/     (1 skill, 1 agent, 1 hook)
    └── makerplace-system/  (3 commands, 2 agents, 1 hook)
```
