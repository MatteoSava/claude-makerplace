---
name: release-readiness
description: Prepare a marketplace-ready release review for the marketplace plugin before publishing.
---

Prepare this package for release.

Check:

- README clarity and first-impression quality
- install instructions and namespaced invocation examples
- command, agent, skill, and hook discoverability
- source inventory and provenance auditability
- CI workflow and local validation parity
- dependency pinning for validation and Python quality hooks
- absence of personal, client, credential, internal URL, local path, or run-specific identifiers
- whether the package tells a coherent engineering story

Run `./bin/makerplace-validate` when command execution is appropriate.

Return a release note draft with:

- release summary
- notable capabilities
- validation evidence
- known limitations
- next improvement steps

$ARGUMENTS
