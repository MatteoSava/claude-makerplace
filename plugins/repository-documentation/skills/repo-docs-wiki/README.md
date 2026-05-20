# Repo Docs Wiki Skill

`repo-docs-wiki` helps an agent build and maintain an LLM-friendly documentation wiki inside a repository's `docs/` directory.

The core idea is simple: source files, tests, configs, existing docs, and git history are the raw truth; `docs/` is the compiled wiki layer that summarizes and links that knowledge; `docs/_meta/schema.md` records the local documentation contract.

## What It Does

- Bootstraps a useful `docs/` structure for repositories with missing or weak documentation.
- Ingests code changes, diffs, PR notes, and user guidance into durable docs pages.
- Answers questions from `docs/` while verifying important implementation claims against source.
- Lints docs for missing frontmatter, stale source references, broken links, orphan pages, and unsupported claims.
- Repairs or reorganizes stale docs without rewriting unrelated content.
- Builds `docs/llms.txt` as a compact routing index for future agent sessions.
- Coordinates read-only subagent fleets for broad repo mapping and docs-fill work.

## When To Use It

Use this skill for requests such as:

- "Document this repo."
- "Create a docs wiki."
- "Update architecture docs from this diff."
- "What do the docs say about this module?"
- "Find stale docs or broken links."
- "Generate an llms.txt for this repository."
- "Launch a fleet of subagents to map the repo and fill the docs."

Do not use it for general code changes unless the user explicitly asks to update documentation as part of the work.

## Default Docs Shape

When there is no strong existing convention, the skill prefers:

```text
docs/
|-- index.md
|-- _meta/
|   |-- schema.md
|   |-- log.md
|   |-- coverage.md
|   `-- lint-report.md
|-- architecture/
|-- modules/
|-- apis/
|-- flows/
|-- runbooks/
|-- concepts/
`-- onboarding.md
```

Existing documentation structure wins unless the user asks for a reorganization.

## Page Contract

Maintained docs pages should include YAML frontmatter:

```yaml
---
title: Human-readable title
type: architecture | module | api | flow | runbook | decision | concept | onboarding | index | meta
summary: One sentence optimized for routing and scanning.
tags: [docs-wiki]
source_refs:
  - path/to/source.py#L10-L42
status: draft | verified | stale | deprecated
updated: YYYY-MM-DD
---
```

Specific technical claims should cite source paths, commits, existing docs pages, or explicit `inference:` notes.

## Script Flow

Run scripts through `uv` from the target repository root. If `CLAUDE_SKILL_DIR` is unavailable, replace it with the absolute path to this skill directory.

| Mode | Script | When to run it |
| --- | --- | --- |
| Bootstrap | `inspect_repo_docs.py` | First read-only check of repo/docs state |
| Bootstrap | `repo_inventory.py` | Before choosing starter docs pages |
| Bootstrap | `init_docs_wiki.py` | Only when `docs/` is missing or empty and the user asked for a docs wiki |
| Fleet map | `inspect_repo_docs.py` and `repo_inventory.py` | Before assigning mapper subagents |
| Ingest | `git_delta.py` | When the changed-file scope is not explicit |
| Ingest/repair | `update_docs_index.py` | After adding, moving, renaming, or changing page frontmatter |
| Lint | `docs_wiki_lint.py` | After docs edits or when asked to lint docs |
| Lint/repair | `check_docs_wiki.py` | Before finishing larger docs work or for a broader health report |
| LLM index | `build_llms_index.py` | When asked for `docs/llms.txt` or compact agent context |

Common commands:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"
uv run python "${CLAUDE_SKILL_DIR}/scripts/repo_inventory.py"
uv run python "${CLAUDE_SKILL_DIR}/scripts/init_docs_wiki.py"
uv run python "${CLAUDE_SKILL_DIR}/scripts/git_delta.py"
uv run python "${CLAUDE_SKILL_DIR}/scripts/update_docs_index.py" docs
uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs
uv run python "${CLAUDE_SKILL_DIR}/scripts/check_docs_wiki.py"
uv run python "${CLAUDE_SKILL_DIR}/scripts/build_llms_index.py" --docs docs --write
```

Scripts are helpers. The agent should still inspect relevant source files and make narrow, source-grounded edits.

## Fleet Map And Fill

For broad documentation requests, the skill can coordinate a subagent fleet:

1. Run repo inspection scripts.
2. Split the repository into 3-6 read-only mapping shards.
3. Ask mapper agents for source refs, missing pages, stale docs, and suggested page summaries.
4. Synthesize findings before writing.
5. Write docs centrally by default, or assign writer agents only to disjoint docs paths.
6. Refresh indexes, lint docs, update coverage, and append the docs log.

Details and prompt templates live in `references/subagent-fleet-workflow.md`.

## Quality Bar

Before finishing a docs update:

- `docs/index.md` links to changed pages.
- Changed pages have frontmatter and a clear summary.
- Specific claims have source references.
- Assumptions and contradictions are labeled.
- New links resolve.
- `docs/_meta/log.md` records the update.
