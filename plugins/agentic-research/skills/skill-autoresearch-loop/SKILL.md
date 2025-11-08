---
name: skill-autoresearch-loop
description: Improve Claude Code skills from real usage feedback. Use when a skill produced a bad result, the user asks for refinement, a workflow gap is discovered, or a repeated fix should be generalized into SKILL.md instructions, hooks, references, or validation.
argument-hint: "[skill name or feedback]"
---

# Skill Autoresearch Loop

Use this skill to make skills self-improving from real work. The output is not just an answer to the current user; it is an improved reusable skill.

## Trigger Conditions

Run this workflow when:

- A user says the agent misunderstood, overreached, missed context, or produced the wrong workflow.
- A skill was used and the next turn asks for a correction or refinement.
- A bug, failed validation, or repeated manual fix exposes a missing instruction.
- A workflow becomes reliable enough to encode as a skill, hook, script, or reference.
- A skill is too project-specific and should be generalized for broader reuse.

## Core Rule

Do not patch only the immediate answer when the lesson is reusable.

Update the impacted skill so the next agent has better behavior without needing the same correction again.

## Workflow

1. Identify the impacted skill.
   - Use the skill invoked in the previous turn when clear.
   - If multiple skills contributed, isolate the instruction that caused the miss.
2. Reconstruct the failure.
   - What did the user expect?
   - What did the agent do?
   - Which instruction was missing, too vague, too strict, or too project-specific?
3. Decide the smallest durable change.
   - Edit `SKILL.md` for behavioral guidance.
   - Add a script only when deterministic checks or repeated commands are needed.
   - Add a reference only when details are useful but too large for the skill body.
   - Add or adjust hooks when the issue should be caught automatically.
4. Generalize.
   - Remove user-specific names, paths, credentials, and local assumptions.
   - Preserve the reusable rule.
   - Prefer short, concrete trigger conditions and workflows.
5. Validate.
   - Check frontmatter.
   - Run plugin or skill validation when available.
   - If code changed, run the relevant quality gate.
6. Record the change.
   - Update README, `.agents.md`, selection maps, or audit docs when the package surface changes.
   - Keep TODO entries current.

## Edit Quality

- Keep skill bodies concise.
- Avoid adding motivational prose.
- Prefer exact trigger language over broad “always” rules.
- Do not duplicate long instructions across skills; cross-reference only when the dependency is stable.
- Do not encode one user’s private workflow as a global public rule.

## Expected Output

Return:

- impacted skill
- failure or feedback captured
- durable skill change made
- validation performed
- remaining gaps, if any
