---
name: intent-system-extension
description: Add a new intent to a deterministic AI behavior or game-agent system. Use when creating an intent type, scoring function, action conversion, executor behavior, feature modifiers, or cooldown rules.
argument-hint: "[intent name]"
---

# Intent System Extension

Use this skill when adding a new intent to an AI behavior system.

## Workflow

1. Add the intent type.
   - Extend the central union/enum/type registry.
2. Add configuration.
   - Weights.
   - thresholds.
   - cooldowns.
   - feature modifiers.
3. Add selection logic.
   - Deterministic scoring function.
   - Personality/state/environment factors.
   - Energy, inventory, risk, or resource constraints when relevant.
4. Add goal/action conversion.
   - Map the chosen intent to concrete actions.
   - Keep action shape compatible with existing planner/executor contracts.
5. Add executor behavior.
   - Only if a new interaction handler is required.
6. Add feature interactions.
   - Bonuses, penalties, or contextual multipliers.
7. Test.
   - Deterministic output with seeded randomness.
   - Intent appears when expected.
   - Intent does not dominate every decision.
   - Cooldown prevents rapid switching.

## Design Rules

- Use the existing RNG/context object for randomness.
- Keep scoring explainable.
- Avoid hidden global state.
- Prefer small additive modifiers over one large opaque rule.
- Preserve backward compatibility for existing intents.

## Expected Output

Return:

- Files touched by layer.
- New scoring factors.
- Cooldown behavior.
- Test cases.
