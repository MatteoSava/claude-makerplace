# Chrome DevTools MCP tool map

Use the current connected tool names. Clients often prefix MCP tools, for example:

```text
mcp__chrome-devtools__take_snapshot
mcp__chrome-devtools__list_console_messages
```

## Navigation

- `list_pages`: enumerate tabs
- `new_page`: create tab and navigate
- `navigate_page`: go to URL, reload, back, forward
- `select_page`: choose active tab
- `wait_for`: wait for text

## Input

- `click`, `hover`, `press_key`
- `fill`: fill one input
- `fill_form`: preferred for multi-field forms
- `type_text`: type into focused input
- `handle_dialog`: accept/dismiss alert/prompt

## Evidence

- `take_snapshot`: preferred DOM/a11y evidence
- `take_screenshot`: visual evidence
- `list_console_messages` / `get_console_message`: runtime evidence
- `list_network_requests` / `get_network_request`: API/asset evidence
- `evaluate_script`: targeted assertions

## Performance and accessibility

- `performance_start_trace`
- `performance_stop_trace`
- `performance_analyze_insight`
- `lighthouse_audit`

## Experimental/high-risk

- extension installation tools
- file upload
- screencast/memory tools
- browser actions against external URLs

Treat these as permissioned operations in `.webqa-devtools/policy.json`.
