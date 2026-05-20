# Troubleshooting

## MCP server not visible

Claude Code:

```text
/mcp
```

Then reinstall if needed:

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

Codex:

```bash
codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

## Browser cannot open

Check:

- Node.js LTS is installed
- npm/npx works
- Chrome is installed
- sandbox/container can launch Chrome
- try `--headless` or `--browser-url=http://127.0.0.1:9222`

## Stop hook keeps blocking

Run:

```bash
python .webqa-devtools/webqa_devtools.py status
```

Then collect evidence with Chrome DevTools MCP, or explicitly record why browser verification is not applicable:

```bash
python .webqa-devtools/webqa_devtools.py mark-verified --kind not-applicable --note "No browser-rendered path changed; only static config was touched."
```

## Hook path is wrong

The example settings assume the command runs from repo root:

```bash
python .webqa-devtools/webqa_devtools.py hook
```

If your agent starts from a subdirectory, use an absolute path or `git rev-parse --show-toplevel` wrapper.
