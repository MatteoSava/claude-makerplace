# Subagent Fleet Workflow

Use this reference when the user asks to launch a fleet of subagents to map a repository and fill `docs/`.

## Goal

Parallelize broad repository inspection without losing source grounding. Subagents gather evidence by shard; the coordinator integrates findings into coherent docs.

## Non-negotiables

- Keep mapper agents read-only. They inspect source and existing docs, then report findings.
- Keep the coordinator responsible for synthesis, conflict resolution, final docs quality, and validation.
- Use writer subagents only when write scopes are disjoint docs paths.
- Do not let agents edit application code, dependencies, generated files, secrets, or CI unless the user explicitly asks for a separate change.
- Every specific claim in generated docs needs a source ref or an `inference:` note.

## Pre-flight

Run these from the target repository root:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"
uv run python "${CLAUDE_SKILL_DIR}/scripts/repo_inventory.py"
```

Use the output to choose shards and identify existing docs, manifests, tests, CI, and source candidates.

If the request is an ingest from recent changes rather than a full bootstrap, also run:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/git_delta.py"
```

## Shard Selection

Prefer 3-6 mapper agents. Use fewer when the repo is small.

Good shard boundaries:

- top-level product or package directories
- public APIs, controllers, routes, or SDK surfaces
- data models, persistence, migrations, schemas, and queues
- user flows, request flows, background jobs, or event flows
- operations: CI, deployment, config, scripts, runbooks
- test and quality signals that reveal expected behavior
- existing docs: stale pages, duplicates, gaps, broken links

Avoid shards that require multiple agents to inspect the same files deeply. If overlap is unavoidable, state the overlap and ask agents to mark uncertainty.

## Mapper Prompt Template

Use one prompt per shard:

```text
You are a read-only docs mapper for the repository.

Scope:
- Inspect only this shard: <paths or domain>
- Read related tests/config/docs when needed for source grounding.
- Do not edit files.

Return:
- Source areas inspected.
- Existing docs pages related to the shard.
- Missing docs pages or sections worth creating.
- Key verified claims with source refs like path/to/file.ext#Lx-Ly.
- Contradictions, stale docs, or uncertain claims.
- Suggested page type: architecture, module, api, flow, runbook, decision, concept, onboarding, or meta.
- Suggested title and one-line summary for each proposed page.
```

## Synthesis

After mappers return:

1. Group findings by proposed page or existing docs page.
2. Deduplicate claims and source refs.
3. Resolve conflicts by checking source directly.
4. Mark unresolved contradictions as questions or `status: draft`.
5. Choose a small first docs set rather than writing every possible page.
6. Define which pages will be created, patched, or left as gaps.

Keep docs cohesive. A page should have a clear reader purpose and not become a dump of every mapper note.

## Writing Docs

Coordinator writes docs by default.

If using writer subagents, assign disjoint write scopes:

```text
You are a docs writer for one page only.

Write scope:
- docs/<path>.md

Inputs:
- Mapper findings below.
- Required page frontmatter contract.

Rules:
- Edit only the assigned docs page.
- Include source_refs in frontmatter.
- Cite specific claims inline or keep them clearly traceable.
- Mark uncertain synthesis as `inference:` or `status: draft`.
- Do not edit source code or other docs pages.
```

The coordinator then reviews all writer output for consistency, links, source refs, and duplicated content.

## Required Integration Updates

After docs pages are written:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/update_docs_index.py" docs
uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs
uv run python "${CLAUDE_SKILL_DIR}/scripts/check_docs_wiki.py"
```

Update manually when needed:

- `docs/_meta/coverage.md`: map source areas to docs pages.
- `docs/_meta/log.md`: append what was mapped, written, skipped, and validated.
- `docs/llms.txt`: run `build_llms_index.py --docs docs --write` when requested or useful for agent routing.

## Final Report

Report:

- mapper shards used
- pages created or updated
- important source areas covered
- unresolved gaps or contradictions
- validation commands and results

