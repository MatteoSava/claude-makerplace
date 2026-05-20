# OpenCode Install

Claude Makerplace supports two OpenCode modes.

## Project-local mode

Run OpenCode from this repository root. OpenCode auto-loads:

- `opencode.json`
- `.opencode/plugins/claude-makerplace.js`
- `.opencode/skills/*`
- `.opencode/commands/*`
- `.opencode/agents/*`

Check discovery:

```bash
opencode debug config
opencode debug skill
```

## Installable plugin mode

The root `package.json` exports `@claude-makerplace/opencode-plugin` from
`opencode-plugin/index.js`.

For local development, add the entrypoint directly to the target OpenCode config:

```json
{
  "plugin": ["file:///path/to/claude-makerplace/opencode-plugin/index.js"]
}
```

After publication to npm, install the module:

```bash
opencode plugin @claude-makerplace/opencode-plugin
```

The plugin registers:

- all marketplace skills by adding the packaged `plugins/` tree to `skills.paths`
- the 4 Makerplace commands from `plugins/makerplace-system/commands`
- the 4 OpenCode adapter agents from `.opencode/agents`
- WebQA and AgentOps skill-local subagents from `plugins/*/skills/*/agents`
- shell environment variables for common skill script directories
- compaction context that explains the cross-agent package layout

## WebQA MCP

Chrome DevTools MCP is opt-in because it can launch a browser helper and inspect
browser state. Enable it with plugin options:

```json
{
  "plugin": [
    ["@claude-makerplace/opencode-plugin", { "enableChromeDevtoolsMcp": true }]
  ]
}
```

Equivalent direct config:

```json
{
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "-y", "chrome-devtools-mcp@latest", "--isolated"],
      "enabled": true,
      "timeout": 20000
    }
  }
}
```

## Individual Skill Install

Some skills also ship repository-level installers with OpenCode adapters:

```bash
uv run python "$MAKERPLACE_WEBQA_DEVTOOLS_SKILL_DIR/scripts/install_webqa_devtools.py" --target . --opencode
uv run python "$MAKERPLACE_AGENTOPS_CONTINUITY_SKILL_DIR/scripts/install_agentops_continuity.py" --target . --opencode
uv run python "$MAKERPLACE_REPO_SENTINEL_SKILL_DIR/scripts/install.py" --target . --opencode
```

When those `MAKERPLACE_*_SKILL_DIR` variables are unavailable, replace them with
the absolute path to the skill directory.

## Hook Limits

OpenCode plugins support config, command, shell, tool, and compaction hooks. They
do not run Claude/Codex hook JSON or provide a direct Stop hook equivalent.
Claude Makerplace maps the portable pieces into OpenCode and documents the rest:

- package context is injected during compaction
- command/script roots are exposed through shell env vars
- WebQA MCP can be registered through plugin options
- Repo Sentinel and AgentOps Stop-gate behavior remains explicit CLI workflow in OpenCode
