# Source Provenance

Claude Makerplace is published as a sanitized package. The public repository does
not include private source paths, internal hosts, credentials, run IDs, or client
identifiers.

## Included Surface

- 23 skills under `plugins/*/skills/*/SKILL.md`
- 4 commands under `plugins/makerplace-system/commands`
- 3 Claude Code plugin agents under `plugins/*/agents`
- 3 runtime hook definitions under `plugins/*/hooks`
- Codex marketplace and plugin manifests, with command hooks loaded from plugin hook directories when enabled
- OpenCode config, runtime plugin, skills links, commands links, and adapter agents

## Provenance Rule

When adding or changing public artifacts, preserve the reusable behavior and
remove local or private context. If a workflow depends on private infrastructure,
describe the integration point generically and keep exact identifiers out of the
package.
