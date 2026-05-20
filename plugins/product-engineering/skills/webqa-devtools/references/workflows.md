# WebQA workflows

## Smoke verification

1. Identify affected route/component.
2. Start dev server or reuse a running server.
3. Navigate with Chrome DevTools MCP.
4. Wait for app ready state.
5. Take a snapshot.
6. Interact with the changed flow.
7. Inspect console messages.
8. Inspect network failures when relevant.
9. Capture screenshot or visual notes when relevant.
10. Write report.

## Bug reproduction

1. Reproduce the browser symptom before patching.
2. Capture console/network/DOM evidence.
3. Map runtime failure to source.
4. Patch minimally.
5. Reproduce again and confirm absence of original symptom.
6. Record before/after evidence.

## Component/design-system change

Use Storybook or a dedicated route if available. Check default, hover, focus, disabled, loading, and error states. For responsive components, test desktop and mobile viewport sizes.

## Performance trace

Run before/after traces when performance is the user-visible requirement. Report method, URL, environment, key bottleneck, and whether the evidence is local lab evidence.

## Accessibility check

Check keyboard navigation, focus order, labels, role/semantics, error messaging, modal/menu escape behavior, and contrast when relevant.
