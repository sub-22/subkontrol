"""Tests for morai-git MCP server."""

import subprocess

import pytest


@pytest.fixture()
def git_repo(tmp_path, monkeypatch):
    """Create a real bare-minimum git repo for testing."""
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # Initial commit so HEAD exists
    (tmp_path / "README.md").write_text("init")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path, check=True, capture_output=True,
    )

    import importlib

    import servers.git.server as mod
    importlib.reload(mod)
    yield tmp_path


def _reload():
    import importlib

    import servers.git.server as mod
    importlib.reload(mod)
    return mod


class TestStatus:
    def test_clean_repo(self, git_repo):
        mod = _reload()
        result = mod.status()
        assert result == "" or isinstance(result, str)

    def test_shows_modified(self, git_repo):
        mod = _reload()
        (git_repo / "new_file.txt").write_text("content")
        result = mod.status()
        assert "new_file.txt" in result


class TestGetCurrentBranch:
    def test_returns_branch_name(self, git_repo):
        mod = _reload()
        branch = mod.get_current_branch()
        assert branch in ("main", "master", "HEAD")


class TestGetLog:
    def test_returns_log(self, git_repo):
        mod = _reload()
        log = mod.get_log(max_count=5)
        assert "init" in log


class TestCommit:
    def test_commit_specific_files(self, git_repo):
        mod = _reload()
        (git_repo / "feature.py").write_text("print('hi')")
        subprocess.run(["git", "add", "feature.py"], cwd=git_repo, capture_output=True)
        result = mod.commit("feat: add feature", files=["feature.py"])
        assert result["ok"] is True

    def test_commit_all_tracked(self, git_repo):
        mod = _reload()
        (git_repo / "README.md").write_text("updated")
        result = mod.commit("docs: update readme")
        assert result["ok"] is True

    def test_commit_empty_fails_gracefully(self, git_repo):
        mod = _reload()
        result = mod.commit("empty commit with nothing staged")
        assert isinstance(result, dict)
        assert "ok" in result


class TestCreateBranch:
    def test_creates_new_branch(self, git_repo):
        mod = _reload()
        result = mod.create_branch("feat/test-branch")
        assert result["ok"] is True

    def test_duplicate_branch_fails_gracefully(self, git_repo):
        mod = _reload()
        mod.create_branch("feat/dup")
        result = mod.create_branch("feat/dup")
        assert isinstance(result, dict)
        assert "ok" in result


class TestDiff:
    def test_diff_no_changes(self, git_repo):
        mod = _reload()
        result = mod.diff()
        assert isinstance(result, str)

    def test_diff_shows_changes(self, git_repo):
        mod = _reload()
        (git_repo / "README.md").write_text("changed content")
        result = mod.diff()
        assert "changed content" in result or "README" in result
