---
name: playwright-ui-validation
description: Validate web UI features with Playwright or browser automation. Use when checking interactive UI behavior, chat flows, theme toggles, cancellation, markdown rendering, auth redirects, or frontend regressions.
argument-hint: "[feature or URL]"
---

# Playwright UI Validation

Use this skill for browser-level validation of frontend features.

## Setup

Before testing:

- Confirm the app URL and required environment.
- Confirm login requirements and test account constraints.
- Confirm the feature's expected behavior.
- Start long-running dev servers in a terminal multiplexer when needed.

## Validation Workflow

1. Open the target page.
2. Wait for the app to become interactive.
3. Exercise the primary user path.
4. Check loading, success, error, cancel, and retry states.
5. Inspect browser console and network failures.
6. Capture screenshots when a visual issue matters.
7. Repeat at a mobile viewport for responsive features.

## Chat UI Checks

- New conversation creation.
- Message send disabled state.
- Streaming partial output.
- Cancel stream.
- Markdown rendering.
- Citation or annotation display.
- Usage metadata after completion.
- Error recovery after failed request.

## Theme and Layout Checks

- Toggle light/dark mode.
- Verify persisted preference if applicable.
- Check text contrast and focus states.
- Confirm no text overflow or overlapping elements on mobile.

## Expected Output

Return:

- Test scenario summary.
- Pass/fail findings with reproduction steps.
- Console or network errors.
- Screenshots or traces saved, if created.
- Follow-up fixes needed.
