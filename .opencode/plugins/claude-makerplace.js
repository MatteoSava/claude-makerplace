const MAKERPLACE_CONTEXT = `
## Claude Makerplace cross-agent context

This repository is a portable agent-workflow marketplace. Claude Code remains
the canonical source layout under plugins/*, with Codex manifests and OpenCode
adapters layered on top.

Multi-agent organization:
- Keep the main agent as coordinator and integrator.
- Delegate broad read-only exploration to reviewer or auditor agents.
- Give implementation agents small, owned write scopes.
- Record unfinished work in TODO.md when work is discovered but intentionally deferred.
- Validate package changes before calling the work complete.

Packaging surfaces:
- Claude Code: .claude-plugin/marketplace.json and plugins/*/.claude-plugin/plugin.json.
- Codex: .agents/plugins/marketplace.json and plugins/*/.codex-plugin/plugin.json.
- OpenCode: opencode.json plus .opencode/skills, .opencode/commands, .opencode/agents, and .opencode/plugins.
`;

export const ClaudeMakerplacePlugin = async ({ client }) => {
  try {
    if (client?.app?.log) {
      await client.app.log({
        body: {
          service: "claude-makerplace",
          level: "info",
          message: "Loaded Claude Makerplace OpenCode adapter",
        },
      });
    }
  } catch {
    // Logging is best-effort and should never block plugin loading.
  }

  return {
    "experimental.session.compacting": async (_input, output) => {
      if (!Array.isArray(output.context)) {
        output.context = [];
      }
      output.context.push(MAKERPLACE_CONTEXT);
    },
  };
};
