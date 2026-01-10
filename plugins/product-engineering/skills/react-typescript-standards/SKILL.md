---
name: react-typescript-standards
description: Apply pragmatic React and TypeScript frontend standards. Use when building components, state reducers, service clients, auth flows, streaming UI, or testable frontend features.
argument-hint: "[frontend task]"
---

# React TypeScript Standards

Use this skill when modifying a React or TypeScript frontend.

## Principles

- Prefer explicit types at module boundaries.
- Keep components focused on rendering and interaction.
- Keep service clients separate from UI state.
- Model complex UI flow with reducers or small state machines.
- Handle loading, empty, error, disabled, and success states.
- Preserve accessibility and keyboard behavior.

## Component Workflow

1. Locate existing design system and component conventions.
2. Define the state shape before coding.
3. Add or update service calls with typed responses.
4. Render all states explicitly.
5. Keep side effects in hooks or service layers.
6. Add tests around behavior, not implementation details.

## Streaming UI Rules

- Use `AbortController` for cancelable requests.
- Parse incremental responses defensively.
- Dispatch typed events to a reducer.
- Keep partial assistant output recoverable after network failure.
- Record usage or completion metadata after the terminal event.

## TypeScript Rules

- Avoid `any` unless interacting with unknown external data at the boundary.
- Narrow unknown data with validation or type guards.
- Prefer discriminated unions for event protocols.
- Keep exported types stable and small.
- Do not leak SDK-specific types through broad app layers unless that is already the project pattern.

## Expected Output

Return:

- State model.
- Component/service boundaries.
- Edge cases handled.
- Test coverage added or still missing.
