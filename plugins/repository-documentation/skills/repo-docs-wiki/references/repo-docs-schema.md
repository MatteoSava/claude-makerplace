# Repo Docs Wiki Schema

This schema adapts the LLM Wiki pattern to project documentation stored under a repository's `docs/` directory.

## Principles

1. **Compiled, not re-derived.** The wiki pages are durable syntheses of the codebase, not temporary chat answers.
2. **Source-grounded.** Every specific claim should point back to code, tests, configs, existing docs, or git metadata.
3. **Incremental.** Use git diffs, changed files, and small edits to keep docs current without rescanning everything.
4. **Human-reviewable.** Keep pages readable, diffs small, and uncertainty explicit.
5. **Portable Markdown.** Use plain Markdown and relative links. Wikilinks are allowed only as an auxiliary convention, not as the only navigation path.

## Page types

| Type | Folder | Purpose | Typical source refs |
|---|---|---|---|
| `index` | `docs/index.md` | Catalog and route map for humans and LLMs | docs pages |
| `meta` | `docs/_meta/` | Schema, log, lint reports, coverage maps | docs pages, git commits |
| `architecture` | `docs/architecture/` | System structure, boundaries, deployment, data ownership | manifests, service entrypoints, configs, diagrams, ADRs |
| `decision` | `docs/architecture/decisions/` | Architecture Decision Records | PR notes, commits, design docs, code changes |
| `module` | `docs/modules/` | Subsystem responsibility and interfaces | source directories, tests, public APIs |
| `api` | `docs/apis/` | API routes, methods, contracts, clients | route definitions, schemas, tests, OpenAPI specs |
| `flow` | `docs/flows/` | End-to-end user/data/request/event flows | controllers, services, tests, message handlers |
| `runbook` | `docs/runbooks/` | Operational procedures and troubleshooting | scripts, deployment config, incident notes, CLI help |
| `concept` | `docs/concepts/` | Domain concepts and vocabulary | models, schemas, tests, docs |
| `onboarding` | `docs/onboarding.md` | How to understand and work on the repo | index, architecture, dev setup |

## Required frontmatter

```yaml
---
title: Human-readable title
type: architecture | module | api | flow | runbook | decision | concept | onboarding | index | meta
summary: One sentence optimized for LLM routing and human scanning.
tags: [docs-wiki]
source_refs:
  - path/to/file.ext#L10-L42
status: draft | verified | stale | deprecated
updated: YYYY-MM-DD
---
```

### Field guidance

- `title`: specific; avoid vague titles like "Overview" unless the page path scopes it.
- `type`: one of the known page types.
- `summary`: one sentence, no marketing language, no unsupported claims.
- `tags`: include `docs-wiki`; add domain tags sparingly.
- `source_refs`: list the most important source refs for the page. Additional section-level refs may appear inline.
- `status`:
  - `draft`: useful but incomplete or not fully verified.
  - `verified`: checked against current source evidence.
  - `stale`: likely outdated; preserve until repaired.
  - `deprecated`: intentionally retained for historical context.
- `updated`: ISO date of the latest docs edit, not necessarily source commit date.

## Citation style

Use compact inline citations:

```md
The API validates requests before dispatching to the service layer. Source: `src/api/routes.py#L24-L61`, `tests/test_api.py#L12-L45`.
```

For section-level evidence:

```md
## Authentication flow

Evidence: `src/auth/session.py#L10-L88`, `src/auth/middleware.py#L18-L72`.

...
```

For synthesis:

```md
Inference: Taken together, `src/a.py#L10-L20` and `tests/test_b.py#L30-L50` imply that retries are idempotent for duplicate request IDs.
```

## Naming rules

- Use kebab-case filenames: `payment-retry-policy.md`.
- Prefer stable project nouns: `billing-module.md`, not `new-billing-stuff.md`.
- Do not encode status in filenames; use `status` frontmatter.
- ADR filenames should be sortable: `0001-use-postgres-for-events.md`.

## Link rules

- Use relative Markdown links for portability: `[Billing module](../modules/billing.md)`.
- Optional Obsidian-style wikilinks may be added in prose, but never as the only link.
- `docs/index.md` should include every maintained page with title, summary, type, and status.
- Each page should include a short `Related pages` section when meaningful.

## Page status transitions

```text
draft -> verified     after source refs are checked
draft -> stale        when source evidence conflicts or is missing
verified -> stale     when git diff or lint shows relevant source changed
stale -> verified     after repair
verified -> deprecated when behavior is intentionally retired
```

## What not to document as fact

- Guessed architecture from filenames alone.
- Behavior inferred from comments when tests/code contradict it.
- Future plans unless explicitly labeled as `Planned` or `Open question`.
- Secrets, credentials, customer data, or internal data not already appropriate for repo docs.
