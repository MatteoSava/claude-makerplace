# Repo Docs Wiki Page Templates

Copy these templates into `docs/` pages as needed. Replace placeholders and remove irrelevant sections.

## Architecture overview

```md
---
title: Architecture Overview
type: architecture
summary: Describes the repository's major runtime components, boundaries, and data/control flow.
tags: [docs-wiki, architecture]
source_refs:
  - README.md
  - path/to/entrypoint#L1-L80
status: draft
updated: YYYY-MM-DD
---

# Architecture Overview

## System purpose

What the system does, grounded in source evidence.

## Major components

| Component | Responsibility | Evidence |
|---|---|---|
| Component name | Responsibility | `path#Lx-Ly` |

## Boundaries and dependencies

External services, local modules, databases, queues, filesystems.

## Key flows

- [Flow name](../flows/flow-name.md)

## Open questions

- Question that could not be verified from source.

## Related pages

- [Onboarding](../onboarding.md)
```

## Module page

```md
---
title: Module Name
type: module
summary: Explains the responsibility, public interface, dependencies, and tests for this module.
tags: [docs-wiki, module]
source_refs:
  - src/module/path#L1-L120
  - tests/test_module.py#L1-L90
status: draft
updated: YYYY-MM-DD
---

# Module Name

## Responsibility

What this module owns and what it does not own.

## Public interface

Functions, classes, CLI commands, routes, or events exposed by the module.

## Dependencies

- Internal dependencies:
- External dependencies:

## Important behaviors

- Behavior with source ref.

## Tests and verification

- `tests/...#Lx-Ly` covers behavior X.

## Change notes

Recent changes or migration notes.

## Related pages

- [Architecture overview](../architecture/overview.md)
```

## API page

```md
---
title: API Name
type: api
summary: Documents request/response contract, validation, auth, and handlers for this API.
tags: [docs-wiki, api]
source_refs:
  - src/api/routes.py#L1-L100
  - tests/test_api.py#L1-L100
status: draft
updated: YYYY-MM-DD
---

# API Name

## Contract

| Method/Event | Path/Topic | Handler | Evidence |
|---|---|---|---|

## Validation

## Authentication and authorization

## Side effects

## Error handling

## Test coverage

## Related pages
```

## Flow page

```md
---
title: Flow Name
type: flow
summary: Traces an end-to-end user, data, request, or event flow through the repository.
tags: [docs-wiki, flow]
source_refs:
  - src/entry#L1-L50
status: draft
updated: YYYY-MM-DD
---

# Flow Name

## Trigger

## Step-by-step path

1. Step. Evidence: `path#Lx-Ly`.
2. Step. Evidence: `path#Lx-Ly`.

## Data shape

## Failure modes

## Observability

## Related pages
```

## Runbook

```md
---
title: Runbook Name
type: runbook
summary: Operational procedure for diagnosing or executing a recurring project task.
tags: [docs-wiki, runbook]
source_refs:
  - scripts/tool.py#L1-L80
  - .github/workflows/ci.yml#L1-L60
status: draft
updated: YYYY-MM-DD
---

# Runbook Name

## When to use this

## Preconditions

## Procedure

```bash
# Commands here
```

## Expected result

## Troubleshooting

## Rollback

## Related pages
```

## ADR / decision record

```md
---
title: "ADR 0001: Decision title"
type: decision
summary: Records the context, choice, and consequences of a project decision.
tags: [docs-wiki, adr]
source_refs:
  - path/to/source#Lx-Ly
status: verified
updated: YYYY-MM-DD
---

# ADR 0001: Decision title

## Status

Accepted | Proposed | Superseded | Deprecated

## Context

## Decision

## Consequences

## Alternatives considered

## Evidence

- `path#Lx-Ly`

## Related pages
```

## Concept page

```md
---
title: Concept Name
type: concept
summary: Defines a domain or project concept and links to implementation evidence.
tags: [docs-wiki, concept]
source_refs:
  - path/to/model#L1-L50
status: draft
updated: YYYY-MM-DD
---

# Concept Name

## Definition

## Where it appears

## Related behavior

## Open questions

## Related pages
```
