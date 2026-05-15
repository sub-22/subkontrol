"""Tests for cost tracking in pipeline server."""

import pytest


@pytest.fixture(autouse=True)
def tmp_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("MORAI_MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("MORAI_BUDGET_TOKENS", "10000")  # small budget for testing
    import importlib

    import servers.pipeline.server as mod

    importlib.reload(mod)
    yield tmp_path


def _reload():
    import importlib

    import servers.pipeline.server as mod

    importlib.reload(mod)
    return mod


class TestRecordTokenUsage:
    def test_records_usage(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.record_token_usage("PROJ-1", "ba", "haiku", 1000, 500)
        assert result["ok"] is True
        assert result["budget_used_pct"] > 0

    def test_accumulates_across_skills(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.record_token_usage("PROJ-1", "ba", "haiku", 1000, 500)
        mod.record_token_usage("PROJ-1", "pm", "haiku", 800, 400)
        mod.record_token_usage("PROJ-1", "dev", "sonnet", 2000, 800)
        cost = mod.get_pipeline_cost("PROJ-1")
        assert cost["total_tokens"] == (1000 + 500 + 800 + 400 + 2000 + 800)
        assert "ba" in cost["by_skill"]
        assert "pm" in cost["by_skill"]
        assert "dev" in cost["by_skill"]

    def test_80_percent_warning(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        # Budget is 10000, use 8100 (81%)
        result = mod.record_token_usage("PROJ-1", "dev", "sonnet", 5000, 3100)
        assert "WARNING" in result.get("alert", "")

    def test_95_percent_critical(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        # Use 9600 tokens (96%)
        result = mod.record_token_usage("PROJ-1", "dev", "sonnet", 6000, 3600)
        assert "CRITICAL" in result.get("alert", "")

    def test_no_alert_under_80(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        result = mod.record_token_usage("PROJ-1", "ba", "haiku", 1000, 500)
        assert result["alert"] == ""

    def test_nonexistent_pipeline_fails(self, tmp_pipeline):
        mod = _reload()
        result = mod.record_token_usage("PROJ-999", "ba", "haiku", 100, 50)
        assert result["ok"] is False

    def test_estimates_usd(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.record_token_usage("PROJ-1", "ba", "haiku", 1_000_000, 0)
        cost = mod.get_pipeline_cost("PROJ-1")
        # Haiku input: $0.80 per 1M tokens
        assert cost["estimated_usd"] == pytest.approx(0.80, rel=0.01)


class TestGetPipelineCost:
    def test_empty_cost(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        cost = mod.get_pipeline_cost("PROJ-1")
        assert cost["total_tokens"] == 0
        assert cost["budget_used_pct"] == 0.0

    def test_nonexistent_pipeline(self, tmp_pipeline):
        mod = _reload()
        result = mod.get_pipeline_cost("PROJ-999")
        assert "error" in result

    def test_cost_breakdown_by_skill(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.record_token_usage("PROJ-1", "ba", "haiku", 1000, 500)
        cost = mod.get_pipeline_cost("PROJ-1")
        assert cost["by_skill"]["ba"]["input_tokens"] == 1000
        assert cost["by_skill"]["ba"]["output_tokens"] == 500
        assert cost["by_skill"]["ba"]["model"] == "haiku"
        assert cost["by_skill"]["ba"]["calls"] == 1


class TestGetCostSummaryAll:
    def test_multiple_pipelines(self, tmp_pipeline):
        mod = _reload()
        mod.create_pipeline("PROJ-1")
        mod.create_pipeline("PROJ-2")
        mod.record_token_usage("PROJ-1", "ba", "sonnet", 5000, 2000)
        mod.record_token_usage("PROJ-2", "ba", "haiku", 1000, 500)
        summary = mod.get_cost_summary_all()
        # PROJ-1 has more tokens, should be first
        assert summary[0]["ticket_id"] == "PROJ-1"
        assert summary[1]["ticket_id"] == "PROJ-2"

    def test_empty_when_no_pipelines(self, tmp_pipeline):
        mod = _reload()
        result = mod.get_cost_summary_all()
        assert result == []
