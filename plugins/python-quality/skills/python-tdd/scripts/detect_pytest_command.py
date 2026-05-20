#!/usr/bin/env python3
"""Detect likely pytest commands for a Python project.

Stdlib-only helper for Claude Code skills. It prints concise guidance that Claude
can use to choose a runner without loading large config files into context.
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover - older Python fallback
    tomllib = None  # type: ignore[assignment]

ROOT = Path.cwd()


def exists(name: str) -> bool:
    return (ROOT / name).exists()


def read_pyproject() -> dict:
    path = ROOT / "pyproject.toml"
    if not path.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def detect_runner(_pyproject: dict) -> str:
    return "uv run pytest"


def detect_test_roots() -> list[str]:
    roots = []
    for candidate in ("tests", "test", "src", "."):
        if exists(candidate):
            roots.append(candidate)
    return roots or ["tests"]


def detect_source_roots(pyproject: dict) -> list[str]:
    roots: list[str] = []
    if exists("src"):
        roots.append("src")
    project_name = pyproject.get("project", {}).get("name")
    if isinstance(project_name, str):
        package = project_name.replace("-", "_")
        for candidate in (package, f"src/{package}"):
            if exists(candidate):
                roots.append(candidate)
    for path in ROOT.iterdir():
        if (
            path.is_dir()
            and (path / "__init__.py").exists()
            and path.name not in {"tests", "test"}
        ):
            roots.append(path.name)
    return sorted(set(roots))


def main() -> int:
    pyproject = read_pyproject()
    runner = detect_runner(pyproject)
    test_roots = detect_test_roots()
    source_roots = detect_source_roots(pyproject)
    config_files = [
        name
        for name in (
            "pyproject.toml",
            "pytest.ini",
            "tox.ini",
            "noxfile.py",
            "requirements.txt",
            "requirements-dev.txt",
            "uv.lock",
        )
        if exists(name)
    ]

    source_arg = " ".join(f"--cov={root}" for root in source_roots[:3]) or "--cov"
    result = {
        "runner": runner,
        "narrow_test_template": f"{runner} -q -x {{test_path}}::{{test_name}}",
        "related_tests_template": f"{runner} -q -x {{test_path}}",
        "full_suite": f"{runner} -q",
        "coverage": f"{runner} {source_arg} --cov-branch --cov-report=term-missing",
        "test_roots": test_roots,
        "source_roots": source_roots,
        "config_files": config_files,
        "notes": [
            "Prefer existing uv-backed project scripts when repository instructions explicitly document them.",
            "Use the narrow command for Red/Green, then related/full suite after Green and Refactor.",
        ],
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
