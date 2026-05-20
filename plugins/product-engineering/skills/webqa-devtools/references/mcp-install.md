# Chrome DevTools MCP install notes

## Claude Code

MCP only:

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

Plugin mode, which bundles MCP plus upstream DevTools skills:

```text
/plugin marketplace add ChromeDevTools/chrome-devtools-mcp
/plugin install chrome-devtools-mcp@chrome-devtools-plugins
```

Useful checks inside Claude Code:

```text
/mcp
/skills
/hooks
```

## Codex

```bash
codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

Config-file alternative:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--isolated"]
startup_timeout_ms = 20000
```

## Useful modes

- `--isolated`: use a temporary browser profile per server instance.
- `--slim`: smaller tool surface for basic browser automation.
- `--headless`: run without visible Chrome where supported.
- `--browser-url=http://127.0.0.1:9222`: attach to a manually started Chrome with remote debugging.

## Privacy

Chrome DevTools MCP can inspect browser data. Use a test profile and local URLs by default.
