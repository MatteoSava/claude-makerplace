# Repo Docs Wiki Quality Gates

Use these gates before returning from a docs-wiki task.

## Grounding gate

- Technical claims cite code, tests, configs, existing docs, or git metadata.
- Synthesis is labeled as inference when it goes beyond a single source.
- Unverified claims are marked as assumptions or open questions.
- Secrets or sensitive values are not copied into docs.

## Structure gate

- Every maintained page has frontmatter.
- `title`, `type`, `summary`, `tags`, `source_refs`, `status`, and `updated` exist.
- `docs/index.md` lists changed pages.
- `docs/_meta/log.md` records the operation.
- New pages live in the correct folder.

## Navigation gate

- Relative links resolve.
- Important pages include a `Related pages` section.
- Orphan pages are intentional or noted.
- The index routes both humans and agents to the right page.

## Freshness gate

- If git is available, recent relevant source changes were considered.
- Stale pages are marked `status: stale` and not left looking verified.
- Deleted or renamed source files are reflected in source refs or coverage notes.

## Diff hygiene gate

- Edits are surgical and reviewable.
- Generated boilerplate is not excessive.
- Existing human-authored content is preserved unless contradicted by source evidence.
- Formatting is consistent with the repository's existing docs style.

## Useful final response

Always tell the user:

1. Which docs files changed.
2. Which source areas were used as evidence.
3. What was verified vs. still uncertain.
4. Any recommended next ingest/lint step.
