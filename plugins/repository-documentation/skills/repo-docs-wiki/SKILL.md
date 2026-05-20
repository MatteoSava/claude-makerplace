---
name: repo-docs-wiki
description: Use when asked to create, update, query, lint, repair, or reorganize repository docs; docs/ wikis; architecture docs; ADRs; API docs; runbooks; onboarding docs; docs indexes; llms.txt; source-grounded citations; or a subagent fleet to map a repo and fill docs from code, tests, config, and git history.
compatibility: Designed for Agent Skills-compatible coding agents with filesystem access. Optional scripts run through uv and require Python 3.10+ and git.
metadata:
  version: "1.0.0"
  pattern: "karpathy-llm-wiki-for-repository-docs"
---

# Repo Docs Wiki

Turn a repository's `docs/` directory into a living, source-grounded project wiki. The codebase and git history are the immutable raw source layer; `docs/` is the compiled wiki layer; `docs/_meta/schema.md` is the local schema layer.

## Core rule

Read broadly, write narrowly. You may read repository code, tests, manifests, existing docs, and git metadata to understand the project, but by default only edit files under `docs/`. Do not edit application code, generated artifacts, dependencies, secrets, or CI configuration unless the user explicitly asks for that separate change.

## When this skill applies

Use this skill for requests like:

- "create project docs", "document this repo", "make docs/ useful", "build a codebase wiki"
- "ingest the latest changes into docs", "update architecture docs from this diff"
- "what does the repo documentation say about X?", "answer from docs/ and verify against code"
- "lint docs", "find stale docs", "detect broken links/orphan pages/uncited claims"
- "add ADRs", "create onboarding docs", "summarize module responsibilities", "document API flows"
- "launch a fleet of subagents to map the repo and fill the docs"

## LLM wiki pattern adapted to `docs/`

- **Raw sources:** repository code, tests, configs, manifests, existing docs, README, changelog, git diff/log, issue/PR notes supplied by the user. These are source-of-truth inputs. Treat them as read-only during docs work.
- **Wiki:** `docs/`, a structured set of Markdown pages maintained by the agent. Pages summarize, link, compare, and synthesize project knowledge.
- **Schema:** `docs/_meta/schema.md`, plus this skill and the reference files bundled with it. The schema defines page types, frontmatter, source citation rules, and maintenance workflows.

The wiki should compound. Do not rediscover the same architectural knowledge from scratch on every question. Compile it into stable pages, then update those pages incrementally as the repo changes.

## Default `docs/` layout

When bootstrapping or repairing a repo, prefer this structure unless existing docs already have a strong convention:

```text
docs/
|-- index.md                  # content-oriented entrypoint and page catalog
|-- _meta/
|   |-- schema.md             # local docs-wiki conventions
|   |-- log.md                # append-only ingest/query/lint history
|   |-- coverage.md           # map of source areas to docs pages
|   `-- lint-report.md        # latest docs health report, if requested
|-- architecture/
|   |-- overview.md
|   `-- decisions/            # ADRs or decision records
|-- modules/                  # subsystem/module pages
|-- apis/                     # public/internal API docs
|-- flows/                    # user, data, request, or event flows
|-- runbooks/                 # operational procedures
|-- concepts/                 # domain/project concepts
`-- onboarding.md
```

Existing structure wins over this default. Migrate only when the user asks or when the current structure is clearly broken and you explain the proposed change.

## Required page contract

Every maintained wiki page should use YAML frontmatter:

```yaml
---
title: Human-readable title
type: architecture | module | api | flow | runbook | decision | concept | onboarding | index | meta
summary: One sentence optimized for LLM routing and human scanning.
tags: [docs-wiki]
source_refs:
  - path/to/source.py#L10-L42
status: draft | verified | stale | deprecated
updated: YYYY-MM-DD
---
```

For details and templates, read `references/repo-docs-schema.md` and `templates/page-templates.md`.

## Source grounding

Every specific technical claim should be grounded in one of these:

1. `path/to/file.ext#Lx-Ly` when line numbers are stable or freshly inspected.
2. `path/to/file.ext@<commit>` when exact lines are unstable but the source revision matters.
3. `docs/page.md` when the claim is already compiled and that page itself has source refs.
4. `inference:` notes for synthesis that combines multiple sources.

Never invent implementation details. If a claim cannot be verified, mark it as a question, assumption, or gap.

## Script use rules

Scripts are helpers for deterministic inventory, lint, and index generation. They do not replace source inspection or judgment. Run scripts from the target repository root with `uv run python`. If `CLAUDE_SKILL_DIR` is unavailable, replace it with the absolute path to this skill directory.

Use scripts only at the points called out in the operating modes below:

| Script | Use when | Result to use |
| --- | --- | --- |
| `scripts/inspect_repo_docs.py` | Starting bootstrap, fleet mapping, ingest, repair, or lint when repo/docs state is unclear | Read-only summary of repo shape, docs pages, state files, and git changes |
| `scripts/repo_inventory.py` | Bootstrap planning before writing first docs pages | Read-only inventory of manifests, source candidates, tests, CI, and existing docs |
| `scripts/init_docs_wiki.py` | `docs/` is missing/empty and the user asked to create a docs wiki | Writes the starter `docs/` skeleton; inspect and refine generated pages afterward |
| `scripts/git_delta.py` | Ingest scope is not explicit | Read-only changed-file list from last docs checkpoint or current git status |
| `scripts/update_docs_index.py` | Pages were added, moved, renamed, or frontmatter changed | Rewrites `docs/index.md`; avoid if the project has a hand-curated index that should be patched manually |
| `scripts/docs_wiki_lint.py` | After docs edits or when the user asks to lint docs | Deterministic frontmatter, link, source-ref, and orphan-page findings |
| `scripts/check_docs_wiki.py` | Before finishing larger docs work or when the user asks for a health check | Broader deterministic health report; still perform semantic source verification manually |
| `scripts/build_llms_index.py` | User asks for `llms.txt`, compact agent context, or LLM routing | Generates or prints `docs/llms.txt` from page frontmatter |

## Runtime Stop hook

The plugin also ships a command Stop hook. When supported by the host agent and enabled/trusted, the hook runs after a turn only if `docs/` files changed and `docs/_meta/schema.md` identifies a repo-docs wiki. It refreshes `docs/index.md` when safe, then runs `docs_wiki_lint.py` and `check_docs_wiki.py --strict`.

Do not rely on the hook for semantic source verification, bootstrapping, or fleet mapping. Those remain explicit skill workflows. Treat hook failures as unfinished docs work and fix them before reporting completion.

## Operating modes

### 1. Bootstrap

Use when `docs/` is missing, empty, or chaotic.

1. Locate repo root with `git rev-parse --show-toplevel` when possible.
2. Run read-only inspection first:
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"`
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/repo_inventory.py"`
3. If `docs/` is missing or empty, create the minimal skeleton with `uv run python "${CLAUDE_SKILL_DIR}/scripts/init_docs_wiki.py"`.
4. Inspect generated pages and source files. Replace generic placeholders with verified claims and source refs.
5. Draft high-value starter pages: `docs/index.md`, `docs/architecture/overview.md`, `docs/onboarding.md`, and one module/API/flow page only when source evidence is clear.
6. If pages were added or frontmatter changed, refresh `docs/index.md` with `uv run python "${CLAUDE_SKILL_DIR}/scripts/update_docs_index.py" docs` unless the index is hand-curated.
7. Run `uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs`.
8. Add an entry to `docs/_meta/log.md`.
9. Report what was created, what remains unknown, and the next best ingest targets.

### 2. Fleet map and fill

Use when the user asks to "launch a fleet", "map the whole repo", "fill the docs", or otherwise requests broad repository documentation work that benefits from parallel inspection.

1. Run pre-flight inventory:
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"`
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/repo_inventory.py"`
2. Read `references/subagent-fleet-workflow.md`.
3. Split the repo into source-grounded shards such as product areas, APIs, data flows, ops/CI, tests, and existing docs gaps.
4. Launch read-only mapper subagents by shard. Each mapper reports source refs, missing docs, contradictions, and suggested pages; mapper agents do not edit files.
5. Synthesize findings into a docs work plan. Resolve overlaps and contradictions before writing.
6. Write or update docs narrowly. The coordinator writes by default; if writer subagents are used, assign disjoint docs page paths.
7. Refresh indexes and validate:
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/update_docs_index.py" docs`
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs`
   - `uv run python "${CLAUDE_SKILL_DIR}/scripts/check_docs_wiki.py"`
8. Update `docs/_meta/coverage.md` and `docs/_meta/log.md`.
9. Report pages created/updated, source areas covered, unresolved gaps, and validation results.

### 3. Ingest

Use when new source material, code changes, a diff, PR notes, or user guidance should update docs.

1. Determine scope:
   - Use explicit user-supplied files first.
   - If scope is unclear, run `uv run python "${CLAUDE_SKILL_DIR}/scripts/git_delta.py"`.
   - If docs state is unclear, run `uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"`.
2. Read existing `docs/index.md`, `docs/_meta/schema.md`, `docs/_meta/log.md`, and pages likely affected.
3. Classify updates:
   - **new page:** concept/module/API/flow not documented yet.
   - **page extension:** add or refine a section.
   - **contradiction:** new source conflicts with existing docs.
   - **stale/deprecated:** source or behavior was removed/renamed.
4. Produce a triage summary before large edits: pages to add, pages to patch, contradictions, source refs.
5. Patch surgically. Prefer small edits, not whole-file rewrites.
6. Update backlinks/related links, `docs/_meta/coverage.md`, and `docs/_meta/log.md`.
7. If pages were added, moved, or renamed, run `uv run python "${CLAUDE_SKILL_DIR}/scripts/update_docs_index.py" docs` unless the index should be patched manually.
8. Run `uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs`.
9. For broad ingests, run `uv run python "${CLAUDE_SKILL_DIR}/scripts/check_docs_wiki.py"`.

### 4. Query

Use when answering questions about the project docs.

1. Read `docs/index.md` first, then the smallest relevant set of docs pages.
2. If docs location or freshness is unclear, run `uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"` and use it only to choose what to read next.
3. Verify important claims against source files when the answer affects design, implementation, operations, APIs, security, or data correctness.
4. Answer with concise source-grounded references.
5. If the answer reveals a durable insight missing from `docs/`, offer a patch or create it when the user asked for documentation maintenance.

### 5. Lint

Use to health-check docs.

1. Run deterministic checks first:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs
uv run python "${CLAUDE_SKILL_DIR}/scripts/check_docs_wiki.py"
```

2. Then inspect semantically for:

- missing `docs/index.md`, `docs/_meta/schema.md`, or `docs/_meta/log.md`
- pages without frontmatter, summaries, tags, source refs, status, or updated date
- broken Markdown links and orphan pages
- stale source refs: paths no longer exist, renamed modules, deleted APIs
- contradictions between pages and source code
- pages that describe behavior not covered by tests or code
- major source areas with no docs coverage
- overly broad pages that should be split
- duplicate pages describing the same concept

Write a short health report. Only write `docs/_meta/lint-report.md` when the user requested a persisted report.

### 6. Repair/refactor

Use when the docs are stale or disorganized.

1. Run `uv run python "${CLAUDE_SKILL_DIR}/scripts/inspect_repo_docs.py"` and `uv run python "${CLAUDE_SKILL_DIR}/scripts/check_docs_wiki.py"` to identify structural problems.
2. Preserve user-authored content unless it is clearly wrong or duplicated.
3. Merge duplicates by keeping the page with better source refs and redirecting/linking from the weaker page.
4. Mark uncertain content as `status: draft` or `status: stale`, not as truth.
5. Keep diffs reviewable: rename/move in separate steps from content rewrites when possible.
6. If page paths changed, run `uv run python "${CLAUDE_SKILL_DIR}/scripts/update_docs_index.py" docs` or patch the index manually.
7. Run `uv run python "${CLAUDE_SKILL_DIR}/scripts/docs_wiki_lint.py" docs`.

### 7. LLM-readable index

Use when the user asks for `llms.txt`, compact agent context, or a low-token docs entrypoint.

1. Read `docs/index.md` and maintained page frontmatter.
2. Generate or refresh `docs/llms.txt` with `uv run python "${CLAUDE_SKILL_DIR}/scripts/build_llms_index.py" --docs docs --write`.
3. Include page path, title, summary, type, and status.
4. Tell agents to verify implementation-sensitive claims against source before acting.

## Quality gates

Before finishing any docs update:

- `docs/index.md` points to the changed pages.
- Each changed page has frontmatter and a one-line `summary`.
- Specific claims have source refs.
- Contradictions and assumptions are labeled.
- Links added in this pass resolve.
- `docs/_meta/log.md` has an append-only entry.
- The final response tells the user what changed, what was verified, and what remains uncertain.

## Progressive disclosure references

Read these only when needed:

- `references/repo-docs-schema.md` - page taxonomy, frontmatter, citations, naming rules.
- `references/workflows.md` - detailed bootstrap/ingest/query/lint/repair procedures.
- `references/subagent-fleet-workflow.md` - parallel repository mapping and docs-fill workflow.
- `references/quality-gates.md` - review checklist for generated docs.
- `templates/page-templates.md` - copyable Markdown templates for each page type.
