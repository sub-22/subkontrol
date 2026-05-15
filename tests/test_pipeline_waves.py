"""Tests for wave management in pipeline FSM."""

import json

import pytest


@pytest.fixture(autouse=True)
def tmp_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("MORAI_MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("MORAI_PIPELINE_PATH", str(tmp_path / "pipeline"))
    import importlib

    import servers.pipeline.server as mod

    importlib.reload(mod)
    yield tmp_path


def _reload():
    import importlib

    import servers.pipeline.server as mod

    importlib.reload(mod)
    return mod


def _make_pipeline_with_waves(mod, ticket_id="PROJ-1"):
    mod.create_pipeline(ticket_id)
    waves = [
        {"wave": 1, "task_ids": ["TASK-1", "TASK-3"], "rationale": "independent"},
        {"wave": 2, "task_ids": ["TASK-2"], "rationale": "depends on wave 1"},
    ]
    return mod.init_waves(ticket_id, waves)


class TestInitWaves:
    def test_creates_wave_plan(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = _make_pipeline_with_waves(mod)
        assert result["ok"] is True
        assert result["total_waves"] == 2

    def test_wave_structure(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        plan = mod.get_wave_plan("PROJ-1")
        assert len(plan["waves"]) == 2
        assert plan["waves"][0]["task_ids"] == ["TASK-1", "TASK-3"]
        assert plan["waves"][1]["task_ids"] == ["TASK-2"]

    def test_tasks_initialized_pending(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        plan = mod.get_wave_plan("PROJ-1")
        for task_id in ["TASK-1", "TASK-3"]:
            assert plan["waves"][0]["tasks"][task_id]["status"] == "pending"

    def test_missing_pipeline_fails(self, tmp_pipeline):
        mod = _reload()
        result = mod.init_waves("PROJ-999", [{"wave": 1, "task_ids": ["T1"]}])
        assert result["ok"] is False


class TestStartWave:
    def test_start_first_wave(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        result = mod.start_wave("PROJ-1", 1)
        assert result["ok"] is True
        assert len(result["tasks_to_spawn"]) == 2

    def test_tasks_to_spawn_have_branches(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        result = mod.start_wave("PROJ-1", 1)
        branches = [t["worktree_branch"] for t in result["tasks_to_spawn"]]
        assert "feat/PROJ-1-task-1" in branches
        assert "feat/PROJ-1-task-3" in branches

    def test_cannot_start_wave2_before_wave1_committed(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        result = mod.start_wave("PROJ-1", 2)
        assert result["ok"] is False
        assert "committed" in result["error"]

    def test_no_wave_plan_fails(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.start_wave("PROJ-1", 1)
        assert result["ok"] is False


class TestUpdateTaskInWave:
    def test_update_status(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        result = mod.update_task_in_wave(
            "PROJ-1", 1, "TASK-1", "approach_ready", approach_summary="Plan to add user auth"
        )
        assert result["ok"] is True

    def test_update_commit(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        result = mod.update_task_in_wave(
            "PROJ-1", 1, "TASK-1", "committed", commit_sha="abc123", files_changed=["src/user.py"]
        )
        assert result["ok"] is True

    def test_wrong_task_id_fails(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        result = mod.update_task_in_wave("PROJ-1", 1, "TASK-99", "running")
        assert result["ok"] is False


class TestGetWaveStatus:
    def test_all_approaches_ready(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        mod.update_task_in_wave(
            "PROJ-1", 1, "TASK-1", "approach_ready", approach_summary="Approach A"
        )
        mod.update_task_in_wave(
            "PROJ-1", 1, "TASK-3", "approach_ready", approach_summary="Approach B"
        )
        status = mod.get_wave_status("PROJ-1", 1)
        assert status["all_approaches_ready"] is True
        assert status["all_committed"] is False

    def test_all_committed(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        mod.update_task_in_wave("PROJ-1", 1, "TASK-1", "committed", commit_sha="sha1")
        mod.update_task_in_wave("PROJ-1", 1, "TASK-3", "committed", commit_sha="sha3")
        status = mod.get_wave_status("PROJ-1", 1)
        assert status["all_committed"] is True
        assert status["all_approaches_ready"] is True

    def test_approaches_collected(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        mod.update_task_in_wave(
            "PROJ-1", 1, "TASK-1", "approach_ready", approach_summary="Use repository pattern"
        )
        status = mod.get_wave_status("PROJ-1", 1)
        assert "TASK-1" in status["approaches"]
        assert status["approaches"]["TASK-1"] == "Use repository pattern"


class TestCommitWave:
    def test_commit_wave_advances_to_next(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        mod.update_task_in_wave("PROJ-1", 1, "TASK-1", "committed", commit_sha="s1")
        mod.update_task_in_wave("PROJ-1", 1, "TASK-3", "committed", commit_sha="s3")
        result = mod.commit_wave("PROJ-1", 1)
        assert result["ok"] is True
        assert result["next_wave"] == 2
        assert result["all_done"] is False

    def test_commit_last_wave_all_done(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        # Single-wave plan
        mod.init_waves("PROJ-1", [{"wave": 1, "task_ids": ["TASK-1"], "rationale": "only wave"}])
        mod.start_wave("PROJ-1", 1)
        mod.update_task_in_wave("PROJ-1", 1, "TASK-1", "committed", commit_sha="sha")
        result = mod.commit_wave("PROJ-1", 1)
        assert result["ok"] is True
        assert result["all_done"] is True
        assert result["next_wave"] is None

    def test_commit_fails_if_not_all_committed(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        _make_pipeline_with_waves(mod)
        mod.start_wave("PROJ-1", 1)
        mod.update_task_in_wave("PROJ-1", 1, "TASK-1", "committed", commit_sha="s1")
        # TASK-3 still running
        result = mod.commit_wave("PROJ-1", 1)
        assert result["ok"] is False
        assert "TASK-3" in result["error"]


class TestParallelFSMPath:
    def test_pm_done_to_parallel(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        # Walk through FSM to PM_DONE
        mod.transition("PROJ-1", "BA_RUNNING")
        (tmp_pipeline / "specs").mkdir()
        (tmp_pipeline / "specs" / "PROJ-1.md").write_text("spec")
        mod.transition("PROJ-1", "BA_DONE", workspace_root=str(tmp_pipeline))
        mod.transition("PROJ-1", "PM_RUNNING")
        (tmp_pipeline / "tasks" / "PROJ-1").mkdir(parents=True)
        (tmp_pipeline / "tasks" / "PROJ-1" / "index.json").write_text("{}")
        mod.transition("PROJ-1", "PM_DONE", workspace_root=str(tmp_pipeline))
        # Can now go to either sequential or parallel
        result = mod.transition("PROJ-1", "DEV_PARALLEL_RUNNING")
        assert result["ok"] is True

    def test_dev_all_committed_requires_wave_plan_complete(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.init_waves("PROJ-1", [{"wave": 1, "task_ids": ["TASK-1"], "rationale": "r"}])
        # Navigate to DEV_PARALLEL_RUNNING
        state_path = mod.PIPELINE_ROOT / "PROJ-1" / "state.json"
        state = json.loads(state_path.read_text())
        state["state"] = "DEV_PARALLEL_RUNNING"
        state_path.write_text(json.dumps(state))
        # Wave not committed yet → should fail
        result = mod.transition("PROJ-1", "DEV_ALL_COMMITTED", workspace_root=str(tmp_pipeline))
        assert result["ok"] is False
        assert "Precondition failed" in result["error"]
