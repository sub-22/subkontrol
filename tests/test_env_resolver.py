"""Tests for servers/_env.py — three-level credential resolution."""

import importlib
import json

import pytest


def _reload_env():
    import servers._env as mod

    mod._DOTENV = None
    mod._CONFIG = None
    importlib.reload(mod)
    return mod


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Isolate each test from real .env and ~/.morai/config.json on the developer's machine.

    Sets _DOTENV={} and _CONFIG={} (not None) so cached re-reads don't happen.
    Tests that need dotenv/config behaviour reset the relevant cache to None
    and set up their own fixtures before calling resolve().
    """
    empty_global = tmp_path / "empty-morai"
    empty_global.mkdir()
    monkeypatch.setenv("MORAI_GLOBAL_PATH", str(empty_global))

    for key in (
        "JIRA_URL",
        "JIRA_EMAIL",
        "JIRA_TOKEN",
        "CONFLUENCE_URL",
        "CONFLUENCE_EMAIL",
        "CONFLUENCE_TOKEN",
        "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN",
        "SLACK_CHANNEL",
        "GITHUB_TOKEN",
        "BITBUCKET_USERNAME",
        "BITBUCKET_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)

    import servers._env as mod

    mod._DOTENV = {}  # prevent re-read of real .env on disk
    mod._CONFIG = {}  # prevent re-read of real config.json on disk
    yield
    mod._DOTENV = None
    mod._CONFIG = None


class TestEnvVarPriority:
    def test_returns_env_var_when_set(self, monkeypatch):
        monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
        from servers._env import resolve

        assert resolve("JIRA_URL") == "https://jira.example.com"

    def test_ignores_unresolved_plugin_template(self, monkeypatch):
        monkeypatch.setenv("JIRA_URL", "${user_config.JIRA_URL}")
        import servers._env as mod

        # _DOTENV and _CONFIG stay as {} from fixture — dotenv/config won't interfere
        assert mod.resolve("JIRA_URL") == ""

    def test_returns_default_when_missing(self):
        from servers._env import resolve

        assert resolve("JIRA_URL", "fallback") == "fallback"


class TestDotenvFallback:
    def test_reads_dotenv_when_env_missing(self, monkeypatch, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_TOKEN=secret-from-dotenv\n")
        monkeypatch.chdir(tmp_path)

        import servers._env as mod

        mod._DOTENV = None  # force re-read from test's .env
        assert mod.resolve("JIRA_TOKEN") == "secret-from-dotenv"

    def test_ignores_dotenv_unresolved_template(self, monkeypatch, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_TOKEN=${user_config.JIRA_TOKEN}\n")
        monkeypatch.chdir(tmp_path)

        import servers._env as mod

        mod._DOTENV = None  # force re-read from test's .env
        assert mod.resolve("JIRA_TOKEN") == ""


class TestConfigJsonFallback:
    def test_reads_jira_from_config(self, monkeypatch, tmp_path):
        config = {
            "jira": {"url": "https://jira.corp.com", "email": "dev@corp.com", "token": "tok123"}
        }  # noqa: E501
        (tmp_path / "config.json").write_text(json.dumps(config))
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))

        import servers._env as mod

        mod._CONFIG = None  # force re-read from test's config.json

        assert mod.resolve("JIRA_URL") == "https://jira.corp.com"
        assert mod.resolve("JIRA_EMAIL") == "dev@corp.com"
        assert mod.resolve("JIRA_TOKEN") == "tok123"

    def test_reads_confluence_from_config(self, monkeypatch, tmp_path):
        config = {
            "confluence": {"url": "https://wiki.corp.com", "email": "dev@corp.com", "token": "ctok"}
        }  # noqa: E501
        (tmp_path / "config.json").write_text(json.dumps(config))
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("CONFLUENCE_URL") == "https://wiki.corp.com"
        assert mod.resolve("CONFLUENCE_TOKEN") == "ctok"

    def test_reads_slack_from_config(self, monkeypatch, tmp_path):
        config = {"slack": {"bot_token": "xoxb-abc", "app_token": "xapp-xyz", "channel": "#dev"}}
        (tmp_path / "config.json").write_text(json.dumps(config))
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("SLACK_BOT_TOKEN") == "xoxb-abc"
        assert mod.resolve("SLACK_APP_TOKEN") == "xapp-xyz"
        assert mod.resolve("SLACK_CHANNEL") == "#dev"

    def test_missing_config_file_returns_default(self, monkeypatch, tmp_path):
        empty = tmp_path / "no-config"
        empty.mkdir()
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(empty))

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("JIRA_URL", "default") == "default"

    def test_invalid_json_returns_default(self, monkeypatch, tmp_path):
        (tmp_path / "config.json").write_text("not valid json {{{")
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("JIRA_URL", "default") == "default"

    def test_missing_section_returns_default(self, monkeypatch, tmp_path):
        config = {"confluence": {"url": "https://wiki.corp.com"}}
        (tmp_path / "config.json").write_text(json.dumps(config))
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("JIRA_URL", "default") == "default"

    def test_defaults_to_home_morai_when_no_env(self, monkeypatch, tmp_path):
        """MORAI_GLOBAL_PATH unset → falls back to ~/.morai/config.json."""
        fake_home = tmp_path / "home"
        morai_dir = fake_home / ".morai"
        morai_dir.mkdir(parents=True)
        config = {"jira": {"token": "from-home"}}
        (morai_dir / "config.json").write_text(json.dumps(config))

        monkeypatch.delenv("MORAI_GLOBAL_PATH")  # autouse sets it; unset to test HOME fallback
        monkeypatch.setenv("HOME", str(fake_home))

        import servers._env as mod

        mod._CONFIG = None  # force re-read now that MORAI_GLOBAL_PATH is unset

        assert mod.resolve("JIRA_TOKEN") == "from-home"


class TestResolutionPriority:
    def test_env_var_wins_over_config(self, monkeypatch, tmp_path):
        config = {"jira": {"token": "from-config"}}
        (tmp_path / "config.json").write_text(json.dumps(config))
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))
        monkeypatch.setenv("JIRA_TOKEN", "from-env")

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("JIRA_TOKEN") == "from-env"

    def test_dotenv_wins_over_config(self, monkeypatch, tmp_path):
        config = {"jira": {"token": "from-config"}}
        (tmp_path / "config.json").write_text(json.dumps(config))
        (tmp_path / ".env").write_text("JIRA_TOKEN=from-dotenv\n")
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        import servers._env as mod

        mod._DOTENV = None  # re-read from test's .env
        mod._CONFIG = None

        assert mod.resolve("JIRA_TOKEN") == "from-dotenv"

    def test_unknown_key_not_in_map_skips_config(self, monkeypatch, tmp_path):
        config = {"jira": {"token": "tok"}}
        (tmp_path / "config.json").write_text(json.dumps(config))
        monkeypatch.setenv("MORAI_GLOBAL_PATH", str(tmp_path))

        import servers._env as mod

        mod._CONFIG = None

        assert mod.resolve("SOME_UNKNOWN_KEY", "default") == "default"


class TestResolvePath:
    def test_returns_path_object(self, monkeypatch):
        monkeypatch.setenv("WORKSPACE_ROOT", "/tmp/myproject")
        from pathlib import Path

        from servers._env import resolve_path

        result = resolve_path("WORKSPACE_ROOT", ".")
        assert isinstance(result, Path)
        assert str(result) == "/tmp/myproject"
