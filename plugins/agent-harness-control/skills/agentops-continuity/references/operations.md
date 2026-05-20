# Operations

## Bootstrap a task

```bash
python .agentops-continuity/agentops_continuity.py new-task --verification-required "Implement cache invalidation"
```

## Record a decision

```bash
python .agentops-continuity/agentops_continuity.py decision --text "Use write-through invalidation to preserve read consistency."
```

## Record a risk

```bash
python .agentops-continuity/agentops_continuity.py risk --text "Risk: Redis TTL behavior differs in staging. Mitigation: add integration test."
```

## Mark verification

```bash
python .agentops-continuity/agentops_continuity.py mark-verified --kind passed --command "pytest -q"
```

## Verification not applicable

```bash
python .agentops-continuity/agentops_continuity.py mark-verified --kind not-applicable --note "Only documentation was reorganized."
```

## One-shot override

```bash
python .agentops-continuity/agentops_continuity.py allow-stop --reason "Human approved final response."
```

## Reset state

```bash
python .agentops-continuity/agentops_continuity.py reset
```

## Hard reset

```bash
python .agentops-continuity/agentops_continuity.py reset --hard
```
