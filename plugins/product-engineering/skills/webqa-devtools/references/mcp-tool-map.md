# Chrome DevTools MCP tool map

Use the exact tool names exposed by your MCP client. They may be namespaced, for example `mcp__chrome-devtools__navigate_page`.

## Navigation

- `list_pages`
- `new_page`
- `navigate_page`
- `select_page`
- `wait_for`

## Input automation

- `click`
- `hover`
- `fill`
- `fill_form`
- `press_key`
- `type_text`
- `handle_dialog`

## Debugging and evidence

- `take_snapshot`
- `take_screenshot`
- `list_console_messages`
- `get_console_message`
- `list_network_requests`
- `get_network_request`
- `evaluate_script`

## Performance/accessibility

- `performance_start_trace`
- `performance_stop_trace`
- `performance_analyze_insight`
- `lighthouse_audit`
