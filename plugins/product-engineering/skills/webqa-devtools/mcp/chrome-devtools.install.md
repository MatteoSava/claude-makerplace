# Chrome DevTools MCP install notes

## Claude Code

MCP only:

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

Plugin mode, MCP + official Chrome DevTools skills:

```text
/plugin marketplace add ChromeDevTools/chrome-devtools-mcp
/plugin install chrome-devtools-mcp@chrome-devtools-plugins
```

Then inspect:

```text
/mcp
```

## Codex

```bash
codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

Or merge:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--isolated"]
startup_timeout_ms = 20000
```

## Useful server modes

Default:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

Slim/headless for basic tasks:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--slim", "--headless"]
    }
  }
}
```

Isolated profile:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--isolated"]
    }
  }
}
```

Remote debugging port:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    }
  }
}
```

## Privacy note

Chrome DevTools MCP can inspect and modify data in the browser instance. Use an isolated or test profile when possible. Do not expose real user data, tokens, or private sessions to an agent unless explicitly intended.
