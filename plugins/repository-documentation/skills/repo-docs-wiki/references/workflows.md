# Repo Docs Wiki Workflows

## Bootstrap workflow

Use this when a repository has no useful `docs/` wiki yet.

1. **Find root and safety context**
   - Run or mentally perform `git rev-parse --show-toplevel`.
   - Inspect `git status --short` to avoid clobbering active user edits.
   - Do not modify code.

2. **Inventory repository**
   - Top-level files: README, LICENSE, CHANGELOG, package manifests, build files.
   - Source directories: `src/`, `app/`, `lib/`, service folders, packages.
   - Tests: `tests/`, `spec/`, `__tests__/`, integration tests.
   - Runtime/deployment: Docker, Compose, Terraform, Kubernetes, CI.
   - Existing docs and ADRs.

3. **Create structure**
   - `docs/index.md`
   - `docs/_meta/schema.md`
   - `docs/_meta/log.md`
   - `docs/_meta/coverage.md`
   - high-value directories: `architecture/`, `modules/`, `apis/`, `flows/`, `runbooks/`, `concepts/`

4. **Draft initial pages**
   - Architecture overview: based only on strong source evidence.
   - Onboarding page: how to navigate docs and repo.
   - One or more module/API/flow pages only when source refs are clear.

5. **Log and report**
   - Append a `bootstrap` entry to `docs/_meta/log.md`.
   - Tell the user what is verified, draft, and still unknown.

## Ingest workflow

Use this when incorporating new code, PRs, diffs, or docs material.

1. **Scope**
   - Explicit user-specified files win.
   - Else use `git diff --name-status` and/or `git diff --cached --name-status`.
   - Else compare against the last entry in `docs/_meta/log.md` or `docs/_meta/state.json` if present.

2. **Read before writing**
   - `docs/index.md`
   - `docs/_meta/schema.md`
   - `docs/_meta/log.md`
   - candidate pages affected by source changes
   - relevant source files/tests/configs

3. **Classify impact**
   - New concept or module.
   - Existing page needs a small update.
   - Existing docs contradict source.
   - Source removed: mark stale/deprecated or remove content after review.
   - No durable docs impact: log if relevant, otherwise skip.

4. **Triage output**
   Before large edits, produce a short triage:

   ```md
   Ingest triage
   - Add: docs/modules/cache.md from src/cache/*
   - Patch: docs/architecture/overview.md, section "Data flow"
   - Stale: docs/apis/legacy-auth.md no matching route found
   - Open question: retry limit is configured dynamically; no source of default found
   ```

5. **Patch**
   - Prefer `str_replace`/targeted edits over full rewrites.
   - Keep existing good prose and source refs.
   - Add `Open questions` instead of pretending certainty.

6. **Update navigation**
   - `docs/index.md`
   - `docs/_meta/coverage.md`
   - related links on affected pages
   - `docs/_meta/log.md`

7. **Validate**
   - Check links.
   - Check frontmatter.
   - Re-check source refs for pages touched.

## Query workflow

Use this when the user asks about repo knowledge.

1. Read `docs/index.md` and route to the relevant pages.
2. Read the relevant pages.
3. Verify critical claims against source code/tests/configs.
4. Answer with docs refs and source refs.
5. If the answer uncovered durable knowledge missing from docs, propose or make a docs patch depending on the user's ask.

## Lint workflow

Use this for docs health checks.

1. Check structure: required files, page frontmatter, summaries, statuses.
2. Check links: relative Markdown links and optional wikilinks.
3. Check source refs: referenced paths exist; line refs are plausible.
4. Check coverage: major source areas without docs; docs pages without source refs.
5. Check drift: recent git changes touching source areas whose docs were not updated.
6. Check contradictions: compare docs claims to code/tests where evidence is available.
7. Produce a prioritized report:
   - Critical: wrong or misleading docs.
   - High: missing docs for important source areas.
   - Medium: broken links, stale refs, missing frontmatter.
   - Low: style, naming, redundant pages.

## Repair workflow

1. Back up meaning, not necessarily wording.
2. Resolve contradictions in favor of source evidence.
3. Split pages when one page covers unrelated concepts.
4. Merge duplicates when multiple pages compete for the same concept.
5. Mark uncertain sections with `Open questions`.
6. Update indexes and logs last.
