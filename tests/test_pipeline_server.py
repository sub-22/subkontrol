"""Tests for morai-pipeline FSM server."""

import json
import os
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def tmp_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("MORAI_MEMORY_PATH", str(tmp_path / "memory"))
    import importlib
    import servers.pipeline.server as mod
    importlib.reload(mod)
    yield tmp_path


def _reload():
    import importlib
    import servers.pipeline.server as mod
    importlib.reload(mod)
    return mod


class TestCreatePipeline:
    def test_creates_in_idle(self, tmp_pipeline):
        mod = _reload()
        result = mod.create_pipeline("PROJ-1")
        assert result["ok"] is True
        assert result["state"] == "IDLE"

    def test_duplicate_active_fails(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.create_pipeline("PROJ-1")
        assert result["ok"] is False
        assert "đã tồn tại" in result["error"]

    def test_recreate_completed_ok(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        # Force complete state directly
        state_path = mod.PIPELINE_ROOT / "PROJ-1" / "state.json"
        state = json.loads(state_path.read_text())
        state["status"] = "complete"
        state_path.write_text(json.dumps(state))
        result = mod.create_pipeline("PROJ-1")
        assert result["ok"] is True


class TestTransition:
    def test_valid_transition(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.transition("PROJ-1", "BA_RUNNING")
        assert result["ok"] is True
        assert result["from"] == "IDLE"
        assert result["to"] == "BA_RUNNING"

    def test_invalid_transition_blocked(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        # Try to jump from IDLE directly to PM_RUNNING (invalid)
        result = mod.transition("PROJ-1", "PM_RUNNING")
        assert result["ok"] is False
        assert "Invalid transition" in result["error"]

    def test_unknown_state_blocked(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.transition("PROJ-1", "NONEXISTENT_STATE")
        assert result["ok"] is False
        assert "Unknown state" in result["error"]

    def test_nonexistent_pipeline(self, tmp_pipeline):
        mod = _reload()
        result = mod.transition("PROJ-999", "BA_RUNNING")
        assert result["ok"] is False
        assert "chưa tồn tại" in result["error"]

    def test_ba_done_precondition_missing_file(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.transition("PROJ-1", "BA_RUNNING")
        # specs/PROJ-1.md doesn't exist
        result = mod.transition("PROJ-1", "BA_DONE", workspace_root=str(tmp_pipeline))
        assert result["ok"] is False
        assert "Precondition failed" in result["error"]

    def test_ba_done_precondition_passes_with_file(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.transition("PROJ-1", "BA_RUNNING")
        # Create the required spec file
        (tmp_pipeline / "specs").mkdir()
        (tmp_pipeline / "specs" / "PROJ-1.md").write_text("spec content")
        result = mod.transition("PROJ-1", "BA_DONE", workspace_root=str(tmp_pipeline))
        assert result["ok"] is True

    def test_dev_committed_without_pr_url(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.transition("PROJ-1", "BA_RUNNING")
        mod.transition("PROJ-1", "BA_DONE", context={"_skip_precondition": True},
                       workspace_root=str(tmp_pipeline))
        # Navigate to DEV_RUNNING (force via multiple transitions)
        # Simpler: just test the precondition directly
        # Set state to DEV_REVIEWING manually
        state_path = mod.PIPELINE_ROOT / "PROJ-1" / "state.json"
        state = json.loads(state_path.read_text())
        state["state"] = "DEV_REVIEWING"
        state_path.write_text(json.dumps(state))
        result = mod.transition("PROJ-1", "DEV_COMMITTED", workspace_root=str(tmp_pipeline))
        assert result["ok"] is False
        assert "commit_sha" in result["error"] or "pr_url" in result["error"]

    def test_dev_committed_with_pr_url(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        state_path = mod.PIPELINE_ROOT / "PROJ-1" / "state.json"
        state = json.loads(state_path.read_text())
        state["state"] = "DEV_REVIEWING"
        state_path.write_text(json.dumps(state))
        result = mod.transition(
            "PROJ-1", "DEV_COMMITTED",
            context={"pr_url": "https://github.com/org/repo/pull/1"},
            workspace_root=str(tmp_pipeline),
        )
        assert result["ok"] is True


class TestGetState:
    def test_returns_state(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        state = mod.get_state("PROJ-1")
        assert state["state"] == "IDLE"
        assert state["ticket_id"] == "PROJ-1"

    def test_missing_pipeline(self, tmp_pipeline):
        mod = _reload()
        result = mod.get_state("PROJ-999")
        assert "error" in result


class TestBlockPipeline:
    def test_block_from_running(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.transition("PROJ-1", "BA_RUNNING")
        result = mod.block_pipeline("PROJ-1", "Waiting for stakeholder input")
        assert result["ok"] is True
        state = mod.get_state("PROJ-1")
        assert state["state"] == "BLOCKED"
        assert state["blocked_reason"] == "Waiting for stakeholder input"


class TestListPipelines:
    def test_lists_all(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.create_pipeline("PROJ-2")
        pipelines = mod.list_pipelines()
        ids = [p["ticket_id"] for p in pipelines]
        assert "PROJ-1" in ids
        assert "PROJ-2" in ids

    def test_filter_by_status(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.create_pipeline("PROJ-2")
        mod.transition("PROJ-1", "BA_RUNNING")
        mod.block_pipeline("PROJ-1", "reason")

        blocked = mod.list_pipelines(status_filter="blocked")
        assert all(p["status"] == "blocked" for p in blocked)
        assert any(p["ticket_id"] == "PROJ-1" for p in blocked)


class TestGetValidTransitions:
    def test_idle_transitions(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.get_valid_transitions("PROJ-1")
        assert result["current_state"] == "IDLE"
        assert "BA_RUNNING" in result["valid_next"]

    def test_complete_has_no_transitions(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        state_path = mod.PIPELINE_ROOT / "PROJ-1" / "state.json"
        state = json.loads(state_path.read_text())
        state["state"] = "COMPLETE"
        state_path.write_text(json.dumps(state))
        result = mod.get_valid_transitions("PROJ-1")
        assert result["valid_next"] == []
