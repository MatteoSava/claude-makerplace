# Threat model

AgentOps Continuity improves memory and workflow reliability. It is not a security boundary.

## Protected against

- Accidental context loss after compaction or resume.
- Final answer before verification evidence.
- Forgetting touched files and decisions during a long run.
- Accidental agent removal of `.agentops-continuity` state through simple guarded commands.

## Not protected against

- A malicious or compromised agent intentionally bypassing all tools.
- Direct user shell access outside the agent loop.
- Sandboxed command escape.
- Secret exfiltration.
- Incorrect or fabricated verification claims in natural language.

## Recommended pairing

Use with:

- repo-sentinel for deterministic command/path policy.
- CI and test automation.
- Secret scanning.
- Branch protection.
- Human review for infrastructure, production, and security-sensitive changes.
