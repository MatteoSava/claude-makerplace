---
name: skill-evolve
description: Improve an existing skill from user feedback, repeated friction, validation failures, or a missed behavior.
---

Improve the relevant skill instead of only solving the immediate symptom.

Use the `skill-curator` agent when the impacted skill needs a focused rewrite pass. Work from evidence:

- identify the user feedback, failed assumption, repeated manual fix, or validation failure
- identify the impacted `SKILL.md`, hook, script, command, or agent
- generalize the lesson so it helps future users and future projects
- keep the skill concise and operational
- preserve sanitization
- update related docs only if the package surface or install instructions changed
- run the package validator after edits

Do not hardcode the current user's private context. Do not fabricate provenance or history.

Return:

- what changed
- why the behavior now generalizes
- which validation passed
- what remains intentionally out of scope

$ARGUMENTS
