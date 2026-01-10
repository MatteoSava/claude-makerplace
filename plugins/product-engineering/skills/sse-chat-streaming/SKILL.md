---
name: sse-chat-streaming
description: Implement or troubleshoot Server-Sent Events streaming for AI chat applications. Use when building chat streaming endpoints, frontend stream parsing, cancellation, annotations, citations, or token usage completion events.
argument-hint: "[chat streaming task]"
---

# SSE Chat Streaming

Use this skill for production-grade chat streaming over Server-Sent Events.

## Event Contract

Define a small explicit event protocol:

- `conversation`: created or resolved conversation ID.
- `chunk`: text delta.
- `annotation`: citation, file quote, or tool-derived metadata.
- `usage`: prompt tokens, completion tokens, total tokens, duration, cost when available.
- `done`: stream completed normally.
- `error`: recoverable or terminal error.

Keep events JSON-serializable and versionable.

## Backend Workflow

1. Set response headers.
   - `Content-Type: text/event-stream`
   - `Cache-Control: no-cache`
   - Disable proxy buffering if the platform requires it.
2. Resolve conversation state before text deltas.
3. Stream typed chunks from the AI provider or service abstraction.
4. Flush after each event.
5. Respect cancellation tokens or abort signals.
6. Emit a terminal `done` or `error` event.
7. Avoid exposing internal exception details in production.

## Backend Rules

- Prefer typed stream objects over raw strings.
- Use cancellation-aware async iteration.
- Separate text deltas from annotations and usage.
- Validate attachment count, media type, and decoded size before streaming.
- Record usage and finish reason when the provider exposes them.

## Frontend Workflow

1. Start request with an `AbortController`.
2. Parse SSE `data:` lines incrementally.
3. Dispatch events into a reducer or state machine:
   - start stream
   - append chunk
   - attach annotations
   - complete with usage
   - cancel or error
4. Keep the input disabled only while streaming.
5. Restore a coherent state on cancel, network error, and malformed event.

## Verification

- Test normal completion.
- Test cancel while deltas are arriving.
- Test provider error after partial output.
- Test citation/annotation event ordering.
- Test mobile browser behavior.
- Confirm the response is not buffered by local dev proxy, CDN, or hosting platform.

## Expected Output

Return:

- Event schema.
- Backend streaming changes.
- Frontend state flow.
- Cancellation and error behavior.
- Tests and manual checks.
