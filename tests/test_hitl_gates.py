"""Tests for HITL gate management in pipeline server."""

import json
from datetime import UTC, datetime, timedelta

import pytest


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


def _make_pipeline(mod, ticket_id="PROJ-1"):
    mod.create_pipeline(ticket_id)
    return ticket_id


class TestCreateGate:
    def test_creates_pending_gate(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        result = mod.create_gate("PROJ-1", "REVIEW", "Review approach")
        assert result["ok"] is True
        assert result["gate_id"] == "PROJ-1-gate-001"

    def test_gate_id_increments(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        r1 = mod.create_gate("PROJ-1", "REVIEW", "Gate 1")
        r2 = mod.create_gate("PROJ-1", "APPROVE", "Gate 2")
        assert r1["gate_id"] == "PROJ-1-gate-001"
        assert r2["gate_id"] == "PROJ-1-gate-002"

    def test_invalid_gate_type_fails(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        result = mod.create_gate("PROJ-1", "INVALID_TYPE", "question")
        assert result["ok"] is False

    def test_nonexistent_pipeline_fails(self, tmp_pipeline):
        mod = _reload()
        result = mod.create_gate("PROJ-999", "REVIEW", "question")
        assert result["ok"] is False

    def test_pending_gate_count_increments(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "Gate 1")
        mod.create_gate("PROJ-1", "CONFIRM", "Gate 2")
        state = mod.get_state("PROJ-1")
        assert state["pending_gate_count"] == 2

    def test_gate_has_expires_at(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        result = mod.create_gate("PROJ-1", "REVIEW", "q", timeout_minutes=30)
        assert "expires_at" in result
        assert result["expires_at"] != ""

    def test_choice_gate_stores_options(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "CHOICE", "Which approach?",
                         options=["Option A", "Option B", "Option C"])
        gate = mod.get_gate("PROJ-1", "PROJ-1-gate-001")
        assert gate["options"] == ["Option A", "Option B", "Option C"]


class TestResolveGate:
    def test_resolve_pending_gate(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "APPROVE", "Approve?")
        result = mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "approve")
        assert result["ok"] is True
        assert result["response"] == "approve"

    def test_resolved_gate_is_no_longer_pending(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "CONFIRM", "Confirm?")
        mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "confirm")
        pending = mod.get_pending_gates("PROJ-1")
        assert len(pending) == 0

    def test_pending_count_decrements_on_resolve(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "Gate 1")
        mod.create_gate("PROJ-1", "CONFIRM", "Gate 2")
        mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "approve")
        state = mod.get_state("PROJ-1")
        assert state["pending_gate_count"] == 1

    def test_cannot_resolve_already_resolved(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "APPROVE", "q")
        mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "yes")
        result = mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "yes again")
        assert result["ok"] is False
        assert "resolved" in result["error"]

    def test_resolve_nonexistent_fails(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        result = mod.resolve_gate("PROJ-1", "PROJ-1-gate-999", "approve")
        assert result["ok"] is False


class TestGetGate:
    def test_get_existing_gate(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "Review code", context="Some context")
        gate = mod.get_gate("PROJ-1", "PROJ-1-gate-001")
        assert gate["gate_type"] == "REVIEW"
        assert gate["question"] == "Review code"
        assert gate["context"] == "Some context"
        assert gate["status"] == "pending"

    def test_get_nonexistent_gate(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        result = mod.get_gate("PROJ-1", "PROJ-1-gate-999")
        assert "error" in result

    def test_gate_stores_pipeline_state(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.transition("PROJ-1", "BA_RUNNING")
        mod.create_gate("PROJ-1", "REVIEW", "q")
        gate = mod.get_gate("PROJ-1", "PROJ-1-gate-001")
        assert gate["pipeline_state_at_creation"] == "BA_RUNNING"


class TestExpiredGates:
    def test_expired_gate_detected_on_read(self, tmp_pipeline, monkeypatch):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "q", timeout_minutes=1)

        # Manually set expires_at to the past
        gate_path = mod._gate_path("PROJ-1", "PROJ-1-gate-001")
        gate = json.loads(gate_path.read_text())
        past = (datetime.now(UTC) - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M UTC")
        gate["expires_at"] = past
        gate_path.write_text(json.dumps(gate))

        # Reading gate should auto-expire it
        result = mod.get_gate("PROJ-1", "PROJ-1-gate-001")
        assert result["status"] == "expired"
        assert result["resolved_by"] == "timeout"

    def test_expired_gate_not_in_pending(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "q")

        gate_path = mod._gate_path("PROJ-1", "PROJ-1-gate-001")
        gate = json.loads(gate_path.read_text())
        past = (datetime.now(UTC) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M UTC")
        gate["expires_at"] = past
        gate_path.write_text(json.dumps(gate))

        pending = mod.get_pending_gates("PROJ-1")
        assert len(pending) == 0


class TestGetPendingGates:
    def test_returns_only_pending(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "Gate 1")
        mod.create_gate("PROJ-1", "CONFIRM", "Gate 2")
        mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "approve")

        pending = mod.get_pending_gates("PROJ-1")
        assert len(pending) == 1
        assert pending[0]["gate_id"] == "PROJ-1-gate-002"

    def test_empty_when_no_gates(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        pending = mod.get_pending_gates("PROJ-1")
        assert pending == []

    def test_sorted_by_creation(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "First")
        mod.create_gate("PROJ-1", "CONFIRM", "Second")
        pending = mod.get_pending_gates("PROJ-1")
        assert pending[0]["gate_id"] == "PROJ-1-gate-001"
        assert pending[1]["gate_id"] == "PROJ-1-gate-002"


class TestListAllPendingGates:
    def test_across_multiple_pipelines(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.create_pipeline("PROJ-2")
        mod.create_gate("PROJ-1", "REVIEW", "Gate in PROJ-1")
        mod.create_gate("PROJ-2", "UNBLOCK", "Gate in PROJ-2")

        all_gates = mod.list_all_pending_gates()
        ticket_ids = [g["ticket_id"] for g in all_gates]
        assert "PROJ-1" in ticket_ids
        assert "PROJ-2" in ticket_ids

    def test_unblock_sorted_first(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.create_gate("PROJ-1", "REVIEW", "Review gate")
        mod.create_gate("PROJ-1", "UNBLOCK", "Unblock gate")

        all_gates = mod.list_all_pending_gates()
        assert all_gates[0]["gate_type"] == "UNBLOCK"
        assert all_gates[1]["gate_type"] == "REVIEW"

    def test_empty_when_none(self, tmp_pipeline):
        mod = _reload()
        result = mod.list_all_pending_gates()
        assert result == []


class TestCancelGate:
    def test_cancel_pending_gate(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "REVIEW", "q")
        result = mod.cancel_gate("PROJ-1", "PROJ-1-gate-001", "no longer needed")
        assert result["ok"] is True

    def test_cannot_cancel_resolved_gate(self, tmp_pipeline):
        mod = _reload()
        _make_pipeline(mod)
        mod.create_gate("PROJ-1", "APPROVE", "q")
        mod.resolve_gate("PROJ-1", "PROJ-1-gate-001", "yes")
        result = mod.cancel_gate("PROJ-1", "PROJ-1-gate-001")
        assert result["ok"] is False
