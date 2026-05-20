import { existsSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ENTRY_DIR = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(ENTRY_DIR, "..");
const PLUGINS_ROOT = path.join(PACKAGE_ROOT, "plugins");
const OPENCODE_ROOT = path.join(PACKAGE_ROOT, ".opencode");

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
- OpenCode: @claude-makerplace/opencode-plugin, opencode.json, .opencode/skills, .opencode/commands, .opencode/agents, and .opencode/plugins.
`;

const SCRIPT_SKILL_ENV = {
  MAKERPLACE_REPO_DOCS_WIKI_SKILL_DIR: [
    "repository-documentation",
    "repo-docs-wiki",
  ],
  MAKERPLACE_PYTHON_TDD_SKILL_DIR: ["python-quality", "python-tdd"],
  MAKERPLACE_REPO_SENTINEL_SKILL_DIR: [
    "agent-harness-control",
    "repo-sentinel",
  ],
  MAKERPLACE_AGENTOPS_CONTINUITY_SKILL_DIR: [
    "agent-harness-control",
    "agentops-continuity",
  ],
  MAKERPLACE_WEBQA_DEVTOOLS_SKILL_DIR: [
    "product-engineering",
    "webqa-devtools",
  ],
};

function addUnique(list, value) {
  if (!list.includes(value)) {
    list.push(value);
  }
}

function parseScalar(value) {
  const trimmed = value.trim();
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  if (trimmed === "null") return null;
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseSimpleYaml(source) {
  const root = {};
  const stack = [{ indent: -1, value: root }];

  for (const rawLine of source.split("\n")) {
    if (!rawLine.trim() || rawLine.trimStart().startsWith("#")) {
      continue;
    }
    const indent = rawLine.match(/^ */)[0].length;
    const line = rawLine.trim();
    const match = line.match(/^("?[^":]+"?|[^:]+):(?:\s*(.*))?$/);
    if (!match) {
      continue;
    }

    const key = match[1].replace(/^"|"$/g, "");
    const value = match[2] ?? "";
    while (stack.length > 1 && indent <= stack.at(-1).indent) {
      stack.pop();
    }
    const parent = stack.at(-1).value;
    if (value === "") {
      const child = {};
      parent[key] = child;
      stack.push({ indent, value: child });
    } else {
      parent[key] = parseScalar(value);
    }
  }

  return root;
}

function parseMarkdownDefinition(source) {
  if (!source.startsWith("---\n")) {
    return [{}, source.trim()];
  }
  const end = source.indexOf("\n---", 4);
  if (end === -1) {
    return [{}, source.trim()];
  }
  const frontmatter = parseSimpleYaml(source.slice(4, end));
  const body = source.slice(end + 4).replace(/^\s*\n/, "").trim();
  return [frontmatter, body];
}

async function readMarkdownDefinition(file) {
  const source = await readFile(file, "utf8");
  return parseMarkdownDefinition(source);
}

async function collectMarkdownFiles(directory) {
  if (!existsSync(directory)) {
    return [];
  }

  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectMarkdownFiles(fullPath)));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(fullPath);
    }
  }
  return files.sort();
}

function permissionFromClaudeTools(tools) {
  const names = String(tools)
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  const permission = { edit: "deny" };

  if (names.includes("read")) permission.read = "allow";
  if (names.includes("grep")) permission.grep = "allow";
  if (names.includes("glob")) permission.glob = "allow";
  if (names.includes("bash")) permission.bash = { "*": "ask" };
  if (names.includes("edit") || names.includes("write")) permission.edit = "ask";
  if (permission.read === "allow" || permission.grep === "allow") {
    permission.list = "allow";
  }

  return permission;
}

function defaultSkillAgentPermission() {
  return {
    edit: "ask",
    read: "allow",
    list: "allow",
    grep: "allow",
    glob: "allow",
    bash: { "*": "ask" },
    skill: { "*": "allow" },
  };
}

async function registerAgents(config) {
  config.agent = config.agent ?? {};
  const baseAgents = await collectMarkdownFiles(path.join(OPENCODE_ROOT, "agents"));
  const skillAgents = await collectMarkdownFiles(PLUGINS_ROOT).then((files) =>
    files.filter((file) => file.includes(`${path.sep}agents${path.sep}`)),
  );

  for (const file of [...baseAgents, ...skillAgents]) {
    const [frontmatter, prompt] = await readMarkdownDefinition(file);
    const name = frontmatter.name ?? path.basename(file, ".md");
    if (!name || config.agent[name]) {
      continue;
    }

    const agent = {
      description: frontmatter.description ?? `${name} agent`,
      mode: frontmatter.mode ?? "subagent",
      prompt,
    };
    if (frontmatter.model) agent.model = frontmatter.model;
    if (frontmatter.variant) agent.variant = frontmatter.variant;
    if (frontmatter.color) agent.color = frontmatter.color;
    if (frontmatter.permission) {
      agent.permission = frontmatter.permission;
    } else if (frontmatter.tools) {
      agent.permission = permissionFromClaudeTools(frontmatter.tools);
    } else {
      agent.permission = defaultSkillAgentPermission();
    }

    config.agent[name] = agent;
  }
}

async function registerCommands(config) {
  config.command = config.command ?? {};
  const commandFiles = await collectMarkdownFiles(
    path.join(PACKAGE_ROOT, "plugins", "makerplace-system", "commands"),
  );

  for (const file of commandFiles) {
    const [frontmatter, template] = await readMarkdownDefinition(file);
    const name = frontmatter.name ?? path.basename(file, ".md");
    if (!name || config.command[name]) {
      continue;
    }
    config.command[name] = {
      description: frontmatter.description ?? `${name} command`,
      template,
    };
  }
}

function registerSkillsPath(config, input, options) {
  const workspaceRoot = path.resolve(input.worktree ?? input.directory ?? "");
  const packageWorkspace = workspaceRoot === PACKAGE_ROOT;
  if (packageWorkspace && options.forcePackageSkills !== true) {
    return;
  }

  config.skills = config.skills ?? {};
  config.skills.paths = Array.isArray(config.skills.paths)
    ? config.skills.paths
    : [];
  addUnique(config.skills.paths, PLUGINS_ROOT);
}

function registerChromeDevtoolsMcp(config, options) {
  if (options.enableChromeDevtoolsMcp !== true) {
    return;
  }

  config.mcp = config.mcp ?? {};
  if (config.mcp["chrome-devtools"]) {
    return;
  }
  config.mcp["chrome-devtools"] = {
    type: "local",
    command: ["npx", "-y", "chrome-devtools-mcp@latest", "--isolated"],
    enabled: true,
    timeout: 20000,
  };
}

async function configureOpenCode(config, input, options) {
  registerSkillsPath(config, input, options);
  await registerAgents(config);
  await registerCommands(config);
  registerChromeDevtoolsMcp(config, options);
}

function applyShellEnv(output) {
  output.env.CLAUDE_MAKERPLACE_ROOT ??= PACKAGE_ROOT;
  output.env.MAKERPLACE_PLUGINS_ROOT ??= PLUGINS_ROOT;
  output.env.CLAUDE_PLUGIN_ROOT ??= path.join(PACKAGE_ROOT, "plugins", "makerplace-system");

  for (const [name, [plugin, skill]] of Object.entries(SCRIPT_SKILL_ENV)) {
    output.env[name] ??= path.join(PACKAGE_ROOT, "plugins", plugin, "skills", skill);
  }
}

export const ClaudeMakerplacePlugin = async (input, options = {}) => {
  try {
    if (input.client?.app?.log) {
      await input.client.app.log({
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
    config: async (config) => configureOpenCode(config, input, options),
    "shell.env": async (_hookInput, output) => {
      applyShellEnv(output);
    },
    "experimental.session.compacting": async (_hookInput, output) => {
      if (!Array.isArray(output.context)) {
        output.context = [];
      }
      output.context.push(MAKERPLACE_CONTEXT);
    },
  };
};

export default ClaudeMakerplacePlugin;
