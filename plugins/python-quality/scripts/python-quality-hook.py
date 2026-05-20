from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PINNED = {
    "ruff": "0.15.8",
    "pyright": "1.1.409",
    "mypy": "2.0.0",
    "pytest": "9.0.3",
}

PROFILES = {"minimal", "standard", "strict"}
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".opencode",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def hook_output(event_name: str, message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": message,
                }
            }
        )
    )


def stop_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def hooks_disabled() -> bool:
    return os.environ.get("MAKERPLACE_HOOKS", "on").lower() in {
        "0",
        "false",
        "off",
        "disabled",
    }


def hook_profile() -> str:
    value = os.environ.get("MAKERPLACE_HOOK_PROFILE", "standard").lower()
    if value in PROFILES:
        return value
    return "standard"


def read_payload() -> dict[str, object]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_file_path(payload: dict[str, object]) -> Path | None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    candidates = [
        tool_input.get("file_path"),
        tool_input.get("path"),
        payload.get("file_path"),
        payload.get("path"),
    ]
    for value in candidates:
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
    return None


def hook_event_name(payload: dict[str, object]) -> str:
    value = payload.get("hook_event_name")
    return value if isinstance(value, str) else "PostToolUse"


def project_root(start: Path) -> Path:
    current = start.parent if start.is_file() else start
    markers = (
        "uv.lock",
        "pyproject.toml",
        "setup.cfg",
        "mypy.ini",
        "pyrightconfig.json",
        ".git",
    )
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in markers):
            return candidate
    return current


def project_root_from_payload(payload: dict[str, object]) -> Path:
    candidates = [
        payload.get("cwd"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.getcwd(),
    ]
    for value in candidates:
        if isinstance(value, str) and value:
            path = Path(value).expanduser().resolve()
            if path.exists():
                return project_root(path)
    return project_root(Path.cwd())


def uv_prefix(root: Path) -> list[str]:
    command = ["uv", "run"]
    if (root / "uv.lock").exists():
        command.append("--frozen")
    return command


def cache_root() -> Path:
    base = os.environ.get("XDG_CACHE_HOME")
    root = Path(base).expanduser() if base else Path.home() / ".cache"
    path = root / "claude-makerplace"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_command(
    root: Path, label: str, command: list[str], timeout: int = 90
) -> tuple[str, int, str]:
    caches = cache_root()
    env = os.environ.copy()
    env["RUFF_CACHE_DIR"] = str(caches / "ruff")
    env["MYPY_CACHE_DIR"] = str(caches / "mypy")
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(root) if not pythonpath else f"{root}{os.pathsep}{pythonpath}"
    )

    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return label, 127, str(exc)
    except subprocess.TimeoutExpired as exc:
        if isinstance(exc.stdout, bytes):
            output = exc.stdout.decode(errors="replace")
        elif isinstance(exc.stdout, str):
            output = exc.stdout
        else:
            output = ""
        return label, 124, (output + f"\nTimed out after {timeout}s").strip()

    return label, completed.returncode, completed.stdout.strip()


def python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        files.append(path)
    return files


def pytest_targets(root: Path) -> list[str]:
    tests_dir = root / "tests"
    if tests_dir.exists():
        return ["tests"]

    targets: list[str] = []
    for path in python_files(root):
        if path.name.startswith("test_") or path.name.endswith("_test.py"):
            targets.append(os.path.relpath(path, root))
    return targets


def format_result(label: str, code: int, output: str) -> str:
    status = "PASS" if code == 0 else f"FAIL {code}"
    if not output:
        return f"- {label}: {status}"
    trimmed = "\n".join(output.splitlines()[-20:])
    return f"- {label}: {status}\n```text\n{trimmed}\n```"


def run_post_tool_use(payload: dict[str, object], profile: str) -> int:
    file_path = read_file_path(payload)
    if file_path is None or file_path.suffix != ".py" or not file_path.exists():
        return 0

    root = project_root(file_path)
    relative_file = os.path.relpath(file_path, root)

    base = uv_prefix(root)
    checks: list[tuple[str, list[str]]] = [
        (
            "ruff check",
            [
                *base,
                "--with",
                f"ruff=={PINNED['ruff']}",
                "ruff",
                "check",
                relative_file,
            ],
        ),
        (
            "ruff format --check",
            [
                *base,
                "--with",
                f"ruff=={PINNED['ruff']}",
                "ruff",
                "format",
                "--check",
                relative_file,
            ],
        ),
    ]

    if profile in {"standard", "strict"}:
        checks.extend(
            [
                (
                    "pyright",
                    [
                        *base,
                        "--with",
                        f"pyright=={PINNED['pyright']}",
                        "pyright",
                        relative_file,
                    ],
                ),
                (
                    "mypy",
                    [
                        *base,
                        "--with",
                        f"mypy=={PINNED['mypy']}",
                        "mypy",
                        "--show-error-codes",
                        "--hide-error-context",
                        "--no-error-summary",
                        "--cache-dir",
                        str(cache_root() / "mypy"),
                        relative_file,
                    ],
                ),
            ]
        )

    results = [run_command(root, label, command) for label, command in checks]
    failures = [result for result in results if result[1] != 0]

    header = (
        f"Python light quality hook ran with profile `{profile}` for `{relative_file}` "
        f"using pinned tools: "
        f"ruff=={PINNED['ruff']}, pyright=={PINNED['pyright']}, "
        f"mypy=={PINNED['mypy']}."
    )
    body = "\n\n".join(format_result(*result) for result in results)
    if failures:
        hook_output(
            "PostToolUse",
            f"{header}\n\nFailures need attention before calling the Python edit complete:\n\n{body}",
        )
    else:
        hook_output(
            "PostToolUse",
            f"{header}\n\nAll Python light quality checks passed.\n\n{body}",
        )

    return 0


def run_stop(payload: dict[str, object], profile: str) -> int:
    if payload.get("stop_hook_active") is True:
        return 0

    root = project_root_from_payload(payload)
    files = python_files(root)
    if not files:
        return 0

    base = uv_prefix(root)
    relative_files = [os.path.relpath(path, root) for path in files]
    checks: list[tuple[str, list[str], int]] = [
        (
            "ruff check",
            [
                *base,
                "--with",
                f"ruff=={PINNED['ruff']}",
                "ruff",
                "check",
                ".",
            ],
            180,
        ),
        (
            "ruff format --check",
            [
                *base,
                "--with",
                f"ruff=={PINNED['ruff']}",
                "ruff",
                "format",
                "--check",
                ".",
            ],
            180,
        ),
    ]

    if profile in {"standard", "strict"}:
        checks.extend(
            [
                (
                    "pyright",
                    [
                        *base,
                        "--with",
                        f"pyright=={PINNED['pyright']}",
                        "pyright",
                        *relative_files,
                    ],
                    180,
                ),
                (
                    "mypy",
                    [
                        *base,
                        "--with",
                        f"mypy=={PINNED['mypy']}",
                        "mypy",
                        "--show-error-codes",
                        "--hide-error-context",
                        "--no-error-summary",
                        "--cache-dir",
                        str(cache_root() / "mypy"),
                        *relative_files,
                    ],
                    180,
                ),
            ]
        )

        tests = pytest_targets(root)
        if tests:
            checks.append(
                (
                    "pytest full",
                    [
                        *base,
                        "--with",
                        f"pytest=={PINNED['pytest']}",
                        "pytest",
                        "-q",
                        "-o",
                        f"cache_dir={cache_root() / 'pytest'}",
                        *tests,
                    ],
                    240,
                )
            )

    results = [
        run_command(root, label, command, timeout=timeout)
        for label, command, timeout in checks
    ]
    failures = [result for result in results if result[1] != 0]

    if not failures:
        return 0

    header = (
        f"Python Stop quality hook ran with profile `{profile}` in "
        f"`{root}` using pinned tools: ruff=={PINNED['ruff']}, "
        f"pyright=={PINNED['pyright']}, mypy=={PINNED['mypy']}, "
        f"pytest=={PINNED['pytest']}."
    )
    body = "\n\n".join(format_result(*result) for result in results)
    stop_block(
        f"{header}\n\nFix these failures before returning to the user:\n\n{body}"
    )
    return 0


def main() -> int:
    if hooks_disabled():
        return 0

    payload = read_payload()
    profile = hook_profile()
    event_name = hook_event_name(payload)

    if event_name == "Stop":
        return run_stop(payload, profile)
    return run_post_tool_use(payload, profile)


if __name__ == "__main__":
    raise SystemExit(main())
