# Quality gates

## Minimum evidence after frontend changes

The default policy requires these categories after the latest frontend edit:

- `dom_or_visual`: `take_snapshot`, `take_screenshot`, or `lighthouse_audit`
- `runtime`: `list_console_messages`, `get_console_message`, or `evaluate_script`

Optional categories can be added in `.webqa-devtools/policy.json`:

- `network`: `list_network_requests`, `get_network_request`
- `performance`: trace tools
- `accessibility`: `lighthouse_audit`, snapshot, keyboard path

## Acceptable completion

A task is complete when the report states:

- route/URL tested
- flow performed
- files or components changed
- console status
- network status when relevant
- visual/DOM evidence
- remaining risks

## Non-browser exception

When browser verification is not applicable, record it explicitly:

```bash
python .webqa-devtools/webqa_devtools.py mark-verified --kind not-applicable --note "Only docs/test-only files changed; no browser path affected."
```
