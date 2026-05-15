"""Tests for morai-memory MCP server."""

import pytest


@pytest.fixture(autouse=True)
def tmp_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("MORAI_MEMORY_PATH", str(tmp_path / "memory"))
    # Re-import to pick up new env var
    import importlib

    import servers.memory.server as mod
    importlib.reload(mod)
    yield tmp_path / "memory"


def _reload():
    import importlib

    import servers.memory.server as mod
    importlib.reload(mod)
    return mod


class TestRecordEpisode:
    def test_creates_episodes_file(self, tmp_memory):
        mod = _reload()
        mod.record_episode(event="test_event", outcome="success", lesson="works")
        assert (tmp_memory / "episodes.md").exists()

    def test_episode_content(self, tmp_memory):
        mod = _reload()
        mod.record_episode(
            event="deploy_ok",
            outcome="success",
            lesson="deploy script works",
            ticket_id="PROJ-1",
            apply_next="use same script",
        )
        content = (tmp_memory / "episodes.md").read_text()
        assert "deploy_ok" in content
        assert "PROJ-1" in content
        assert "deploy script works" in content
        assert "use same script" in content

    def test_pattern_count_increments(self, tmp_memory):
        mod = _reload()
        mod.record_episode(event="my_event", outcome="success", lesson="l1")
        mod.record_episode(event="my_event", outcome="success", lesson="l2")
        counts = mod.get_pattern_counts()
        assert counts["my_event"] == 2

    def test_returns_count_string(self, tmp_memory):
        mod = _reload()
        result = mod.record_episode(event="ev", outcome="success", lesson="l")
        assert "ev" in result
        assert "1" in result


class TestGetEpisodes:
    def test_empty(self, tmp_memory):
        mod = _reload()
        result = mod.get_episodes()
        assert "Chưa có" in result

    def test_returns_episodes(self, tmp_memory):
        mod = _reload()
        mod.record_episode(event="ev1", outcome="success", lesson="lesson1")
        mod.record_episode(event="ev2", outcome="fail", lesson="lesson2")
        result = mod.get_episodes()
        assert "ev1" in result
        assert "ev2" in result

    def test_filter_by_event(self, tmp_memory):
        mod = _reload()
        mod.record_episode(event="auth_fail", outcome="fail", lesson="bad token")
        mod.record_episode(event="deploy_ok", outcome="success", lesson="good")
        result = mod.get_episodes(filter_event="auth_fail")
        assert "auth_fail" in result
        assert "deploy_ok" not in result

    def test_limit(self, tmp_memory):
        mod = _reload()
        for i in range(5):
            mod.record_episode(event=f"event_{i}", outcome="success", lesson=f"l{i}")
        result = mod.get_episodes(limit=2)
        # Should only contain last 2 events
        assert "event_3" in result
        assert "event_4" in result
        assert "event_0" not in result


class TestPreferences:
    def test_get_empty(self, tmp_memory):
        mod = _reload()
        result = mod.get_preferences()
        assert "Chưa có" in result

    def test_update_and_get(self, tmp_memory):
        mod = _reload()
        mod.update_preference("coding_style.indent", "2 spaces")
        result = mod.get_preferences()
        assert "coding_style.indent" in result
        assert "2 spaces" in result

    def test_update_replaces_existing(self, tmp_memory):
        mod = _reload()
        mod.update_preference("coding_style.indent", "2 spaces")
        mod.update_preference("coding_style.indent", "4 spaces")
        result = mod.get_preferences()
        assert "4 spaces" in result
        assert result.count("coding_style.indent") == 1

    def test_update_multiple_keys(self, tmp_memory):
        mod = _reload()
        mod.update_preference("key_a", "val_a")
        mod.update_preference("key_b", "val_b")
        result = mod.get_preferences()
        assert "key_a" in result
        assert "key_b" in result


class TestReflexCandidates:
    def test_no_candidates_below_threshold(self, tmp_memory):
        mod = _reload()
        mod.record_episode(event="rare_event", outcome="success", lesson="l")
        mod.record_episode(event="rare_event", outcome="success", lesson="l")
        candidates = mod.get_reflex_candidates(min_count=3)
        assert len(candidates) == 0

    def test_candidate_at_threshold(self, tmp_memory):
        mod = _reload()
        for _ in range(3):
            mod.record_episode(event="repeated_event", outcome="success", lesson="l")
        candidates = mod.get_reflex_candidates(min_count=3)
        assert any(c["pattern"] == "repeated_event" for c in candidates)

    def test_promote_to_reflex(self, tmp_memory):
        mod = _reload()
        for _ in range(3):
            mod.record_episode(event="promote_me", outcome="success", lesson="l")
        result = mod.promote_to_reflex(
            pattern="promote_me",
            trigger="when X happens",
            action="do Y automatically",
        )
        assert "promote_me" in result
        reflexes = mod.get_reflexes()
        assert "promote_me" in reflexes


class TestPipelineState:
    def test_save_and_get(self, tmp_memory):
        mod = _reload()
        mod.save_pipeline_state("PROJ-42", {"current_step": "ba", "status": "active"})
        state = mod.get_pipeline_state("PROJ-42")
        assert state["ticket_id"] == "PROJ-42"
        assert state["current_step"] == "ba"

    def test_get_nonexistent(self, tmp_memory):
        mod = _reload()
        result = mod.get_pipeline_state("PROJ-999")
        assert "error" in result

    def test_list_active_pipelines(self, tmp_memory):
        mod = _reload()
        mod.save_pipeline_state("PROJ-1", {"current_step": "dev", "status": "active"})
        mod.save_pipeline_state("PROJ-2", {"current_step": "qa", "status": "complete"})
        active = mod.list_active_pipelines()
        ticket_ids = [p["ticket_id"] for p in active]
        assert "PROJ-1" in ticket_ids
        assert "PROJ-2" not in ticket_ids
