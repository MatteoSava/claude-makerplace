---
name: internal-wiki-query
description: Query an internal documentation assistant through MCP or another tool. Use when the user asks about organization-specific processes, platform conventions, governance, security rules, or DevOps documentation and a configured knowledge-base tool exists.
argument-hint: "[documentation question]"
---

# Internal Wiki Query

Use this skill for organization-specific documentation questions.

## Workflow

1. Identify the configured documentation tool.
2. Ask the user's question directly with enough context.
3. Preserve citations returned by the tool.
4. Separate documented facts from inference.
5. If the tool is unavailable, state that and fall back to local repository docs.

## Guardrails

- Do not invent internal policy.
- Do not expose private endpoint URLs or credentials in the final answer.
- When citations conflict, prefer the newest authoritative document.
- Keep the answer operational: what to do, where to check, and what remains uncertain.

## Expected Output

Return:

- Direct answer.
- Cited source titles or paths when available.
- Any unresolved ambiguity.
- Next action if documentation is missing.
