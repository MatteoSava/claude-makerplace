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


def hook_output(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                }
            }
        )
    )


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


def read_file_path() -> Path | None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return None

    candidates = [
        payload.get("tool_input", {}).get("file_path"),
        payload.get("tool_input", {}).get("path"),
        payload.get("file_path"),
        payload.get("path"),
    ]
    for value in candidates:
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
    return None


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


def matching_tests(root: Path, file_path: Path) -> list[Path]:
    if file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
        return [file_path]

    stem = file_path.stem
    names = {f"test_{stem}.py", f"{stem}_test.py"}
    matches: list[Path] = []

    direct_candidates = [file_path.with_name(name) for name in names]
    direct_candidates.extend((root / "tests" / name) for name in names)

    for candidate in direct_candidates:
        if candidate.exists():
            matches.append(candidate)

    tests_dir = root / "tests"
    if tests_dir.exists():
        for candidate in tests_dir.rglob("*.py"):
            if candidate.name in names and candidate not in matches:
                matches.append(candidate)
            if len(matches) >= 5:
                break

    return matches[:5]


def format_result(label: str, code: int, output: str) -> str:
    status = "PASS" if code == 0 else f"FAIL {code}"
    if not output:
        return f"- {label}: {status}"
    trimmed = "\n".join(output.splitlines()[-20:])
    return f"- {label}: {status}\n```text\n{trimmed}\n```"


def main() -> int:
    if hooks_disabled():
        return 0

    file_path = read_file_path()
    if file_path is None or file_path.suffix != ".py" or not file_path.exists():
        return 0

    profile = hook_profile()
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

    tests = matching_tests(root, file_path)
    if profile in {"standard", "strict"} and tests:
        checks.append(
            (
                "pytest targeted",
                [
                    *base,
                    "--with",
                    f"pytest=={PINNED['pytest']}",
                    "pytest",
                    "-q",
                    "-o",
                    f"cache_dir={cache_root() / 'pytest'}",
                    *[os.path.relpath(path, root) for path in tests],
                ],
            )
        )

    tests_dir = root / "tests"
    if profile == "strict" and tests_dir.exists():
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
                    "tests",
                ],
            )
        )

    results = [run_command(root, label, command) for label, command in checks]
    failures = [result for result in results if result[1] != 0]

    header = (
        f"Python quality hook ran with profile `{profile}` for `{relative_file}` "
        f"using pinned tools: "
        f"ruff=={PINNED['ruff']}, pyright=={PINNED['pyright']}, "
        f"mypy=={PINNED['mypy']}, pytest=={PINNED['pytest']}."
    )
    body = "\n\n".join(format_result(*result) for result in results)
    if failures:
        hook_output(
            f"{header}\n\nFailures need attention before calling the Python edit complete:\n\n{body}"
        )
    else:
        hook_output(f"{header}\n\nAll Python quality checks passed.\n\n{body}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
