import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import plugin from "../opencode-plugin/index.js";

const tempWorkspace = await mkdtemp(path.join(tmpdir(), "makerplace-opencode-"));
const input = {
  client: { app: { log: async () => undefined } },
  directory: tempWorkspace,
  worktree: tempWorkspace,
  experimental_workspace: { register: () => undefined },
  serverUrl: new URL("http://127.0.0.1"),
  $: {},
};

const hooks = await plugin(input);
assert.equal(typeof hooks.config, "function");
assert.equal(typeof hooks["shell.env"], "function");
assert.equal(typeof hooks["experimental.session.compacting"], "function");

const config = {};
await hooks.config(config);

assert.ok(config.skills.paths.some((item) => item.includes("/plugins/") && item.endsWith("/skills")));
assert.ok(config.command["marketplace-health"].template.includes("Audit this"));
assert.ok(config.command["feedback-makerplace"].description.includes("feedback"));
assert.ok(config.agent["makerplace-lead"].prompt.includes("lead agent"));
assert.ok(config.agent["browser-debugger"].prompt.includes("first goal is reproduction"));
assert.ok(config.agent["context-curator"].prompt.includes("context curator"));
assert.equal(config.mcp, undefined);

const envOutput = { env: {} };
await hooks["shell.env"]({ cwd: tempWorkspace }, envOutput);
assert.ok(envOutput.env.CLAUDE_MAKERPLACE_ROOT);
assert.ok(envOutput.env.MAKERPLACE_REPO_DOCS_WIKI_SKILL_DIR.endsWith("repo-docs-wiki"));
assert.ok(envOutput.env.MAKERPLACE_WEBQA_DEVTOOLS_SKILL_DIR.endsWith("webqa-devtools"));

const compactOutput = { context: [] };
await hooks["experimental.session.compacting"]({ sessionID: "s1" }, compactOutput);
assert.ok(compactOutput.context.join("\n").includes("Claude Makerplace"));

const mcpHooks = await plugin(input, { enableChromeDevtoolsMcp: true });
const mcpConfig = {};
await mcpHooks.config(mcpConfig);
assert.deepEqual(mcpConfig.mcp["chrome-devtools"].command, [
  "npx",
  "-y",
  "chrome-devtools-mcp@latest",
  "--isolated",
]);

console.log("opencode-plugin-smoke-ok");
