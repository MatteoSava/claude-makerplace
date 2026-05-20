# WebQA verification playbook

## Smoke test

Use for every UI change:

1. Start or reuse the app.
2. Open the route.
3. Take a snapshot.
4. Perform the user action.
5. Check console messages.
6. Check network requests if APIs/assets are involved.
7. Capture screenshot for visual changes.
8. Write report.

Pass criteria:

- target UI state is visible
- no relevant console errors
- no relevant failed network requests
- visual state matches expected behavior
- flow can be repeated from a clean page load

## Debug test

1. Reproduce before editing.
2. Preserve failure evidence.
3. Identify root cause.
4. Patch minimally.
5. Re-run the exact flow.
6. Confirm the original failure signal is gone.

## Regression test

When a bug is fixed, add one of:

- unit/component test for pure logic or component behavior
- Playwright/Cypress test for route-level behavior
- regression report if automated test is not feasible

## Browser evidence matrix

| Area | Evidence |
|---|---|
| DOM/UI state | `take_snapshot`, screenshot |
| Runtime | console messages |
| API/assets | network request list/details |
| Performance | trace + insight |
| Accessibility | snapshot + lighthouse + keyboard path |
| Responsive | resize/emulate + screenshot/snapshot |
