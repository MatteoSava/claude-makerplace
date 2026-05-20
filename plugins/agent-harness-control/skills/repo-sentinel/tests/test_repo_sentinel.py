import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "assets" / "project_scaffold" / ".repo-sentinel" / "repo_sentinel.py"
INSTALLER = ROOT / "scripts" / "install.py"

spec = importlib.util.spec_from_file_location("repo_sentinel", SCRIPT)
assert spec is not None
assert spec.loader is not None
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


def run_hook(tmp_path, payload):
    env = dict(**__import__("os").environ)
    p = tmp_path / ".repo-sentinel"
    p.mkdir(parents=True, exist_ok=True)
    (p / "policy.json").write_text(json.dumps(rs.default_policy()), encoding="utf-8")
    cp = subprocess.run(
        [sys.executable, str(SCRIPT), "hook"],
        input=json.dumps({"cwd": str(tmp_path), **payload}),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    return cp


def test_blocks_git_reset(tmp_path):
    cp = run_hook(
        tmp_path,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git reset --hard"},
        },
    )
    assert cp.returncode == 0
    out = json.loads(cp.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_secret_path_write(tmp_path):
    cp = run_hook(
        tmp_path,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": ".env"},
        },
    )
    out = json.loads(cp.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_allows_safe_command(tmp_path):
    cp = run_hook(
        tmp_path,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python -m pytest"},
        },
    )
    assert cp.returncode == 0
    assert cp.stdout.strip() == ""


def test_patch_path_extraction(tmp_path):
    patch = "*** Begin Patch\n*** Update File: src/app.py\n@@\n-x\n+y\n*** End Patch"
    paths = rs.extract_paths_from_patch(tmp_path, patch)
    assert paths == ["src/app.py"]


def test_installer_writes_opencode_skill(tmp_path):
    target = tmp_path / "repo"
    completed = subprocess.run(
        [sys.executable, str(INSTALLER), "--target", str(target), "--opencode"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stdout
    assert (target / ".opencode/skills/repo-sentinel/SKILL.md").exists()
    config = json.loads(
        (target / ".opencode/opencode.repo-sentinel.example.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["permission"]["skill"]["*"] == "allow"
