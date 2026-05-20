---
name: webqa-devtools
description: Verify and debug web UI changes in a real Chrome browser using Chrome DevTools MCP. Use for frontend smoke tests, console/network failures, accessibility, responsive layout, performance traces, and when repository hooks require browser evidence.
---

# WebQA DevTools for Codex

Use Chrome DevTools MCP to verify web app behavior in the browser before declaring success.

Workflow:

1. Run `python .webqa-devtools/webqa_devtools.py preflight`.
2. Use the local app URL from `.webqa-devtools/policy.json` unless the user provides a different safe URL.
3. Navigate with Chrome DevTools MCP.
4. Prefer `take_snapshot` for DOM/a11y tree evidence.
5. Check `list_console_messages` for runtime errors.
6. Check `list_network_requests` for failed API/static asset requests when relevant.
7. Use `take_screenshot` for visual/layout evidence.
8. Use `lighthouse_audit` for accessibility/best-practices checks.
9. Use performance trace tools for load or interaction performance problems.
10. Write a report under `.webqa-devtools/reports/`.

Do not use production/sensitive URLs by default. Do not type secrets into browser pages. Redact tokens and cookies from reports.

Useful commands:

```bash
python .webqa-devtools/webqa_devtools.py status
python .webqa-devtools/webqa_devtools.py report --title "webqa verification" --result Partial
python .webqa-devtools/webqa_devtools.py mark-verified --kind manual --note "Verified manually in Chrome"
```
