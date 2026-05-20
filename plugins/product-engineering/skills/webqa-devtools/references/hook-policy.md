# Hook policy

The hook pack is deterministic. It does not attempt to run browser automation itself; instead it tracks whether browser evidence exists and blocks completion when policy says evidence is required.

## Events

- `SessionStart`: inject current WebQA state.
- `UserPromptSubmit`: remind the agent of local WebQA rules.
- `PreToolUse`: block risky Chrome DevTools actions such as external navigation and sensitive headers.
- `PostToolUse`: record frontend edits, verification commands, and browser evidence.
- `Stop`: block completion when frontend changes lack required evidence.

## Why this shape

Browser verification is agentic and stateful, so it belongs in the skill/subagents. Safety and stop gates are deterministic, so they belong in hooks.

## Stop gate

The default Stop gate requires:

- `dom_or_visual` evidence after latest frontend change
- `runtime` evidence after latest frontend change

It does not require `network` evidence unless you add it to `minimum_browser_evidence_categories`.

## Manual override

Manual verification is explicit and logged:

```bash
python .webqa-devtools/webqa_devtools.py mark-verified --kind manual --note "reason"
```

Use it when browser verification is impossible or not applicable, not as a shortcut.
