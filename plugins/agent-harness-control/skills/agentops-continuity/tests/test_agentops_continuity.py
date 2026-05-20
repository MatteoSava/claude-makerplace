from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SCAFFOLD = PACKAGE / "assets" / "project_scaffold"
SCRIPT_SRC = SCAFFOLD / ".agentops-continuity" / "agentops_continuity.py"
POLICY_SRC = SCAFFOLD / ".agentops-continuity" / "policy.json"
INSTALLER = PACKAGE / "scripts" / "install_agentops_continuity.py"


def make_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    app = repo / ".agentops-continuity"
    app.mkdir(parents=True)
    shutil.copy2(SCRIPT_SRC, app / "agentops_continuity.py")
    shutil.copy2(POLICY_SRC, app / "policy.json")
    return repo, app / "agentops_continuity.py"


def run_hook(
    repo: Path, script: Path, payload: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "hook"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=repo,
        timeout=10,
    )


def test_user_prompt_creates_task_and_injects_context(tmp_path: Path):
    repo, script = make_repo(tmp_path)
    res = run_hook(
        repo,
        script,
        {
            "hook_event_name": "UserPromptSubmit",
            "cwd": str(repo),
            "session_id": "s1",
            "prompt": "Implement a small parser change",
        },
    )
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    task = json.loads(
        (repo / ".agentops-continuity/state/current-task.json").read_text()
    )
    assert task["verification_required"] is True
    assert "parser" in task["objective"]


def test_precompact_writes_snapshot(tmp_path: Path):
    repo, script = make_repo(tmp_path)
    res = run_hook(
        repo,
        script,
        {
            "hook_event_name": "PreCompact",
            "cwd": str(repo),
            "session_id": "s1",
            "trigger": "manual",
            "custom_instructions": "",
        },
    )
    assert res.returncode == 0, res.stderr
    snaps = list((repo / ".agentops-continuity/state/snapshots").glob("*.md"))
    assert snaps


def test_postcompact_records_summary(tmp_path: Path):
    repo, script = make_repo(tmp_path)
    res = run_hook(
        repo,
        script,
        {
            "hook_event_name": "PostCompact",
            "cwd": str(repo),
            "session_id": "s1",
            "trigger": "auto",
            "compact_summary": "We changed src/a.py and still need tests.",
        },
    )
    assert res.returncode == 0, res.stderr
    latest = repo / ".agentops-continuity/state/latest-compact-summary.md"
    assert latest.exists()
    assert "need tests" in latest.read_text()


def test_stop_blocks_when_verification_required(tmp_path: Path):
    repo, script = make_repo(tmp_path)
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "new-task",
            "--verification-required",
            "Fix parser",
        ],
        cwd=repo,
    )
    res = run_hook(
        repo,
        script,
        {
            "hook_event_name": "Stop",
            "cwd": str(repo),
            "session_id": "s1",
            "stop_hook_active": False,
            "last_assistant_message": "Done",
        },
    )
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["decision"] == "block"
    assert "requires verification" in out["reason"]


def test_mark_verified_allows_stop(tmp_path: Path):
    repo, script = make_repo(tmp_path)
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "new-task",
            "--verification-required",
            "Fix parser",
        ],
        cwd=repo,
    )
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "mark-verified",
            "--kind",
            "passed",
            "--command",
            "pytest -q",
        ],
        cwd=repo,
    )
    res = run_hook(
        repo,
        script,
        {
            "hook_event_name": "Stop",
            "cwd": str(repo),
            "session_id": "s1",
            "stop_hook_active": False,
            "last_assistant_message": "Done",
        },
    )
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == ""


def test_posttool_records_touched_file_and_verification(tmp_path: Path):
    repo, script = make_repo(tmp_path)
    subprocess.check_call(
        [sys.executable, str(script), "new-task", "Implement feature"], cwd=repo
    )
    res = run_hook(
        repo,
        script,
        {
            "hook_event_name": "PostToolUse",
            "cwd": str(repo),
            "session_id": "s1",
            "tool_name": "Write",
            "tool_input": {"file_path": str(repo / "src/app.py")},
        },
    )
    assert res.returncode == 0, res.stderr
    task = json.loads(
        (repo / ".agentops-continuity/state/current-task.json").read_text()
    )
    assert "src/app.py" in task["touched_files"]
    assert task["verification_required"] is True
    res2 = run_hook(
        repo,
        script,
        {
            "hook_event_name": "PostToolUse",
            "cwd": str(repo),
            "session_id": "s1",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest -q"},
        },
    )
    assert res2.returncode == 0, res2.stderr
    ver = json.loads(
        (repo / ".agentops-continuity/state/verification-status.json").read_text()
    )
    assert ver["status"] == "passed"


def test_installer_writes_opencode_adapter(tmp_path: Path):
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
    assert (target / ".opencode/skills/agentops-continuity/SKILL.md").exists()
    agent = target / ".opencode/agents/context-curator.md"
    assert agent.exists()
    assert "mode: subagent" in agent.read_text(encoding="utf-8")
    config = json.loads(
        (target / ".opencode/opencode.agentops-continuity.example.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["permission"]["skill"]["*"] == "allow"
