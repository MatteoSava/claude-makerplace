---
name: marketplace-health
description: Audit the installed marketplace plugin for marketplace readiness, sanitization, hook health, and validation drift.
---

Audit this Claude Code engineering marketplace package.

Use the `marketplace-auditor` agent when a separate review pass would be useful. Focus on:

- marketplace and plugin manifests
- skill frontmatter and naming consistency
- command and agent discoverability
- hook wiring and hook profiles
- documentation accuracy
- source inventory, selection map, and provenance consistency
- leak markers, local paths, private identifiers, credentials, and internal URLs
- CI validation and local validation parity

Run `./bin/makerplace-validate` from the package root when command execution is appropriate.

Return:

- findings ordered by severity
- exact files to change
- validation commands already run
- residual risk before publishing

$ARGUMENTS
