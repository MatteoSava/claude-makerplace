<!-- WEBQA-DEVTOOLS-INSTRUCTIONS -->
# WebQA DevTools repository instructions

For UI/frontend work, do not rely only on code inspection. Verify the relevant route or flow in Chrome using Chrome DevTools MCP, then write evidence to `.webqa-devtools/reports/`.

Required evidence after frontend edits:

- DOM/visual evidence: `take_snapshot` or `take_screenshot`
- Runtime evidence: `list_console_messages`
- Network evidence when relevant: `list_network_requests`

Use:

```bash
python .webqa-devtools/webqa_devtools.py preflight
python .webqa-devtools/webqa_devtools.py status
python .webqa-devtools/webqa_devtools.py report --title "<task>"
```

Default policy allows localhost browser verification and blocks external navigation unless `.webqa-devtools/policy.json` is changed.
