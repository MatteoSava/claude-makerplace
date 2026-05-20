#!/usr/bin/env python3
"""Initialize a repo-docs-wiki skeleton under docs/.

Safe by default: creates missing files and directories, but does not overwrite
existing content unless --force is supplied.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

SCHEMA = """---
title: Repo Docs Wiki Schema
type: meta
summary: Defines the local conventions for the repository documentation wiki.
tags: [docs-wiki, schema]
source_refs: []
status: verified
updated: {today}
---

# Repo Docs Wiki Schema

This `docs/` directory is maintained as a source-grounded project wiki.

## Layers

- Raw sources: repository code, tests, configs, manifests, existing docs, and git history.
- Wiki: Markdown pages under `docs/`.
- Schema: this file and the installed `repo-docs-wiki` skill.

## Required frontmatter

```yaml
title: Human-readable title
type: architecture | module | api | flow | runbook | decision | concept | onboarding | index | meta
summary: One sentence optimized for routing and scanning.
tags: [docs-wiki]
source_refs:
  - path/to/source#L10-L42
status: draft | verified | stale | deprecated
updated: YYYY-MM-DD
```

## Source refs

Use `path#Lx-Ly` for code/test/config evidence, `path@commit` for revision-level evidence, and `inference:` labels for synthesis.
"""

INDEX = """---
title: Documentation Index
type: index
summary: Catalog of the repository documentation wiki.
tags: [docs-wiki, index]
source_refs: []
status: draft
updated: {today}
---

# Documentation Index

This index routes humans and LLM agents to the maintained project documentation.

## Core pages

- [Architecture overview](architecture/overview.md) - system structure and major components.
- [Onboarding](onboarding.md) - how to navigate and work with this repository.
- [Schema](_meta/schema.md) - documentation conventions.
- [Coverage](_meta/coverage.md) - source-to-docs coverage map.
- [Log](_meta/log.md) - append-only maintenance history.

## Architecture

_To be populated._

## Modules

_To be populated._

## APIs

_To be populated._

## Flows

_To be populated._

## Runbooks

_To be populated._

## Concepts

_To be populated._
"""

LOG = """---
title: Repo Docs Wiki Log
type: meta
summary: Append-only history of docs wiki bootstrap, ingest, query, lint, and repair operations.
tags: [docs-wiki, log]
source_refs: []
status: verified
updated: {today}
---

# Repo Docs Wiki Log

## [{today}] bootstrap | initialized docs wiki skeleton

- Created baseline docs-wiki structure.
- Next: ingest source-grounded architecture, module, API, and flow pages.
"""

COVERAGE = """---
title: Docs Coverage Map
type: meta
summary: Tracks which repository source areas are covered by docs pages.
tags: [docs-wiki, coverage]
source_refs: []
status: draft
updated: {today}
---

# Docs Coverage Map

| Source area | Docs page | Status | Notes |
|---|---|---|---|
| _To be mapped_ |  | draft | Run an ingest pass to populate this table. |
"""

ARCH = """---
title: Architecture Overview
type: architecture
summary: Draft overview of the repository architecture; verify and enrich during ingest.
tags: [docs-wiki, architecture]
source_refs: []
status: draft
updated: {today}
---

# Architecture Overview

## System purpose

_To be filled from source evidence._

## Major components

| Component | Responsibility | Evidence |
|---|---|---|

## Key flows

_To be linked after flow ingest._

## Open questions

- What are the primary runtime entrypoints?
- What are the external dependencies and deployment boundaries?

## Related pages

- [Documentation Index](../index.md)
"""

ONBOARDING = """---
title: Repository Onboarding
type: onboarding
summary: Starting point for understanding and contributing to this repository.
tags: [docs-wiki, onboarding]
source_refs: []
status: draft
updated: {today}
---

# Repository Onboarding

## Start here

1. Read [Documentation Index](index.md).
2. Read [Architecture Overview](architecture/overview.md).
3. Inspect the source refs cited by the pages you rely on.

## How this docs wiki works

The pages under `docs/` are maintained as compiled knowledge from repository source evidence. Treat pages with `status: verified` as source-checked; treat `draft` and `stale` pages as needing review.

## Common tasks

_To be populated during ingest._
"""


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def write_file(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize docs/ as a repo docs wiki."
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to initialize."
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing seed files."
    )
    args = parser.parse_args()

    today = dt.date.today().isoformat()
    docs = Path(args.docs_dir)
    created: list[str] = []

    for rel in [
        "_meta",
        "architecture/decisions",
        "modules",
        "apis",
        "flows",
        "runbooks",
        "concepts",
    ]:
        (docs / rel).mkdir(parents=True, exist_ok=True)

    files = {
        "index.md": INDEX.format(today=today),
        "_meta/schema.md": SCHEMA.format(today=today),
        "_meta/log.md": LOG.format(today=today),
        "_meta/coverage.md": COVERAGE.format(today=today),
        "architecture/overview.md": ARCH.format(today=today),
        "onboarding.md": ONBOARDING.format(today=today),
    }

    for rel, content in files.items():
        if write_file(docs / rel, content, args.force):
            created.append(str(docs / rel))

    state = {
        "schema_version": "1.0.0",
        "last_bootstrap_commit": git_commit(),
        "last_ingested_commit": None,
    }
    if write_file(
        docs / "_meta" / "state.json", json.dumps(state, indent=2) + "\n", args.force
    ):
        created.append(str(docs / "_meta" / "state.json"))

    print("repo-docs-wiki initialized")
    if created:
        print("created/updated:")
        for item in created:
            print(f"  - {item}")
    else:
        print("no files changed; use --force to overwrite seed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
