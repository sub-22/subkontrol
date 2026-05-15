"""Tests for morai-events server."""

import pytest


@pytest.fixture(autouse=True)
def tmp_events(tmp_path, monkeypatch):
    monkeypatch.setenv("MORAI_MEMORY_PATH", str(tmp_path / "memory"))
    import importlib

    import servers.events.server as mod
    importlib.reload(mod)
    yield tmp_path


def _reload():
    import importlib

    import servers.events.server as mod
    importlib.reload(mod)
    return mod


class TestListEventTypes:
    def test_returns_known_types(self, tmp_events):
        mod = _reload()
        types = mod.list_event_types()
        assert "github.pr_opened" in types
        assert "cron.weekly_friday" in types
        assert "internal.tasks_completed_10" in types


class TestSubscribe:
    def test_creates_subscription(self, tmp_events):
        mod = _reload()
        result = mod.subscribe("github.pr_opened", "/morai:reviewer")
        assert result["ok"] is True
        assert result["subscription_id"].startswith("sub-")

    def test_invalid_event_type_fails(self, tmp_events):
        mod = _reload()
        result = mod.subscribe("nonexistent.event", "/morai:reviewer")
        assert result["ok"] is False
        assert "Unknown event_type" in result["error"]

    def test_subscription_with_filter(self, tmp_events):
        mod = _reload()
        mod.subscribe("github.pr_opened", "/morai:reviewer",
                       filter_conditions={"branch_prefix": "feat/"})
        subs = mod.get_subscriptions("github.pr_opened")
        user_subs = [s for s in subs if s["subscription_id"].startswith("sub-")]
        assert len(user_subs) == 1
        assert user_subs[0]["filter"]["branch_prefix"] == "feat/"


class TestUnsubscribe:
    def test_deactivates_subscription(self, tmp_events):
        mod = _reload()
        result = mod.subscribe("github.pr_opened", "/morai:reviewer")
        sub_id = result["subscription_id"]
        mod.unsubscribe(sub_id)
        subs = mod.get_subscriptions("github.pr_opened", active_only=True)
        ids = [s["subscription_id"] for s in subs]
        assert sub_id not in ids

    def test_nonexistent_fails(self, tmp_events):
        mod = _reload()
        result = mod.unsubscribe("sub-999")
        assert result["ok"] is False


class TestGetSubscriptions:
    def test_default_subscriptions_loaded(self, tmp_events):
        mod = _reload()
        subs = mod.get_subscriptions()
        assert len(subs) > 0
        types = [s["event_type"] for s in subs]
        assert "github.pr_opened" in types

    def test_filter_by_event_type(self, tmp_events):
        mod = _reload()
        subs = mod.get_subscriptions(event_type="github.pr_opened")
        assert all(s["event_type"] == "github.pr_opened" for s in subs)

    def test_inactive_excluded_by_default(self, tmp_events):
        mod = _reload()
        # jira.ticket_in_progress is disabled by default
        all_subs = mod.get_subscriptions("jira.ticket_in_progress", active_only=False)
        active_subs = mod.get_subscriptions("jira.ticket_in_progress", active_only=True)
        assert len(all_subs) >= 1
        assert len(active_subs) == 0  # disabled by default


class TestPublish:
    def test_triggers_matching_handlers(self, tmp_events):
        mod = _reload()
        result = mod.publish("github.pr_opened", {"pr_number": 45, "branch": "feat/test"})
        assert result["ok"] is True
        assert len(result["handlers_to_trigger"]) > 0
        handlers = [h["handler"] for h in result["handlers_to_trigger"]]
        assert "/morai:reviewer" in handlers

    def test_no_handlers_for_unsubscribed_event(self, tmp_events):
        mod = _reload()
        # github.push has no default subscription
        result = mod.publish("github.push", {"branch": "main"})
        assert result["ok"] is True
        assert len(result["handlers_to_trigger"]) == 0

    def test_filter_branch_prefix_match(self, tmp_events):
        mod = _reload()
        mod.subscribe("github.pr_opened", "/morai:custom",
                       filter_conditions={"branch_prefix": "feat/PROJ-123"})
        # Matching branch
        result = mod.publish("github.pr_opened", {"branch": "feat/PROJ-123-auth"})
        handlers = [h["handler"] for h in result["handlers_to_trigger"]]
        assert "/morai:custom" in handlers

    def test_filter_branch_prefix_no_match(self, tmp_events):
        mod = _reload()
        mod.subscribe("github.pr_opened", "/morai:custom",
                       filter_conditions={"branch_prefix": "feat/PROJ-999"})
        result = mod.publish("github.pr_opened", {"branch": "feat/PROJ-123-auth"})
        handlers = [h["handler"] for h in result["handlers_to_trigger"]]
        assert "/morai:custom" not in handlers

    def test_event_logged(self, tmp_events):
        mod = _reload()
        mod.publish("github.pr_merged", {"pr_number": 10})
        log = mod.get_event_log(limit=10, event_type="github.pr_merged")
        assert len(log) == 1
        assert log[0]["event_type"] == "github.pr_merged"

    def test_multiple_publishes_logged(self, tmp_events):
        mod = _reload()
        mod.publish("github.pr_opened", {"pr_number": 1})
        mod.publish("github.pr_opened", {"pr_number": 2})
        log = mod.get_event_log(event_type="github.pr_opened")
        assert len(log) == 2


class TestGetEventLog:
    def test_empty_initially(self, tmp_events):
        mod = _reload()
        log = mod.get_event_log()
        assert log == []

    def test_limit_respected(self, tmp_events):
        mod = _reload()
        for i in range(5):
            mod.publish("internal.pipeline_blocked", {"ticket_id": f"PROJ-{i}"})
        log = mod.get_event_log(limit=3)
        assert len(log) == 3

    def test_filter_by_type(self, tmp_events):
        mod = _reload()
        mod.publish("github.pr_opened", {})
        mod.publish("github.pr_merged", {})
        log = mod.get_event_log(event_type="github.pr_opened")
        assert len(log) == 1
        assert log[0]["event_type"] == "github.pr_opened"


class TestCronGuide:
    def test_returns_guide(self, tmp_events):
        mod = _reload()
        guide = mod.get_cron_setup_guide()
        assert "CronCreate" in guide
        assert "kaizen" in guide
        assert "evolve" in guide
