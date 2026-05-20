<!-- WEBQA-DEVTOOLS-INSTRUCTIONS -->
# WebQA DevTools repository instructions

When frontend/UI files change, verify the local app in Chrome before finishing. Use Chrome DevTools MCP if available and record evidence under `.webqa-devtools/reports/`.

Minimum browser evidence after frontend changes:

- DOM/visual: `take_snapshot` or `take_screenshot`
- Runtime: `list_console_messages`
- Network: `list_network_requests` when APIs/assets are involved

Local helper:

```bash
python .webqa-devtools/webqa_devtools.py status
python .webqa-devtools/webqa_devtools.py preflight
python .webqa-devtools/webqa_devtools.py report --title "<task>"
```

Default safety: local URLs only unless the user and `.webqa-devtools/policy.json` explicitly allow external URLs.
