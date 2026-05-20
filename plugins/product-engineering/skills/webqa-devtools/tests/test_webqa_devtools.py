from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "assets" / "project_scaffold"
SCRIPT = SCAFFOLD / ".webqa-devtools" / "webqa_devtools.py"


def load_module():
    spec = importlib.util.spec_from_file_location("webqa_devtools", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_external_url_blocked_by_default():
    mod = load_module()
    policy = mod.load_json(SCAFFOLD / ".webqa-devtools" / "policy.json", {})
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__chrome-devtools__navigate_page",
        "tool_input": {"url": "https://example.com"},
    }
    result = mod.pre_tool_policy(event, policy)
    assert result
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_localhost_url_allowed():
    mod = load_module()
    policy = mod.load_json(SCAFFOLD / ".webqa-devtools" / "policy.json", {})
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__chrome-devtools__navigate_page",
        "tool_input": {"url": "http://localhost:3000/login"},
    }
    assert mod.pre_tool_policy(event, policy) is None


def test_extract_paths_from_apply_patch():
    mod = load_module()
    patch = """*** Begin Patch
*** Update File: src/App.tsx
@@
- old
+ new
*** Add File: src/styles.css
*** End Patch
"""
    paths = mod.extract_paths_from_patch(patch)
    assert "src/App.tsx" in paths
    assert "src/styles.css" in paths


def test_frontend_glob_detection():
    mod = load_module()
    policy = mod.load_json(SCAFFOLD / ".webqa-devtools" / "policy.json", {})
    assert mod.is_frontend_file("src/components/Button.tsx", policy)
    assert not mod.is_frontend_file("src/components/Button.test.tsx", policy)
    assert not mod.is_frontend_file("node_modules/foo/index.js", policy)


def test_artifact_path_guard():
    mod = load_module()
    policy = mod.load_json(SCAFFOLD / ".webqa-devtools" / "policy.json", {})
    ok, _ = mod.artifact_path_allowed(".webqa-devtools/reports/screen.png", policy)
    assert ok
    ok, reason = mod.artifact_path_allowed("secrets/screen.png", policy)
    assert not ok
    assert "outside allowed" in reason
