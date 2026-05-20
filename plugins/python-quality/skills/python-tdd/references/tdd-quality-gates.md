# TDD quality gates

## Red gate

A Red phase is valid when all are true:

- The test expresses one observable behavior.
- The failure is expected and meaningful.
- The failure would be fixed by implementing the requested behavior, not by changing paths, imports, or test setup.
- The test would fail against at least one plausible wrong implementation.
- The test does not encode private implementation details unless the private detail is the public contract of the unit under test.

Invalid Red examples:

- Syntax error in the test.
- Import error caused by the test using the wrong module path.
- Test passes immediately.
- Test only asserts that a mock was called but not that a useful outcome occurred.
- Snapshot created from unknown output without an explicit expected behavior.

## Green gate

A Green phase is valid when all are true:

- The current Red test passes.
- Existing related tests pass.
- The implementation is the smallest change that satisfies the behavior.
- No test was weakened, skipped, deleted, or rewritten just to pass.
- No unrelated production behavior was modified.

Accept simple or even slightly ugly code during Green. Save cleanup for Refactor.

## Refactor gate

A Refactor phase is valid when all are true:

- No behavior changes were intended.
- Tests pass after the refactor.
- The code is simpler by at least one measurable dimension: less duplication, clearer names, smaller function, lower branching, better boundary, or less coupling.
- Public API changes are absent unless the current behavior explicitly required them.

## Test smell checklist

Investigate before continuing when a test has:

- Multiple unrelated reasons to fail.
- Large fixture setup that hides the behavior.
- Assertions on private methods or call order with no public outcome.
- Real sleeps, real time, real network, or real randomness.
- Shared global state that leaks across tests.
- Overuse of mocks for simple value objects.
- Coverage of implementation branches with no user-visible contract.

## AI-agent guardrails

Common AI mistakes to prevent:

- Writing implementation and tests in the same step during Red.
- Creating a test that passes immediately because the model pre-implemented the behavior.
- Overfitting the implementation to one narrow assertion when additional acceptance criteria were already stated.
- Refactoring before confirming Green.
- Expanding scope to "clean up" unrelated modules.
- Treating coverage percentage as proof of quality.
