"""Tests for morai-file MCP server."""

import pytest


@pytest.fixture(autouse=True)
def tmp_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    import importlib

    import servers.file.server as mod
    importlib.reload(mod)
    yield tmp_path


def _reload():
    import importlib

    import servers.file.server as mod
    importlib.reload(mod)
    return mod


class TestReadFile:
    def test_read_existing(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / "test.txt").write_text("hello world")
        assert mod.read_file("test.txt") == "hello world"

    def test_read_missing_returns_error(self, tmp_workspace):
        mod = _reload()
        result = mod.read_file("nonexistent.txt")
        assert result.startswith("ERROR:")

    def test_read_directory_returns_error(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / "adir").mkdir()
        result = mod.read_file("adir")
        assert result.startswith("ERROR:")


class TestWriteFile:
    def test_write_artifact_path(self, tmp_workspace):
        mod = _reload()
        result = mod.write_file("specs/PROJ-1.md", "spec content")
        assert (tmp_workspace / "specs" / "PROJ-1.md").read_text() == "spec content"
        assert "ERROR" not in result

    def test_write_rejects_source_path(self, tmp_workspace):
        mod = _reload()
        result = mod.write_file("src/main.py", "code")
        assert result.startswith("ERROR")
        assert not (tmp_workspace / "src" / "main.py").exists()

    def test_write_reviews_allowed(self, tmp_workspace):
        mod = _reload()
        result = mod.write_file("reviews/PROJ-1-review.md", "review")
        assert "ERROR" not in result

    def test_write_tasks_allowed(self, tmp_workspace):
        mod = _reload()
        result = mod.write_file("tasks/PROJ-1/index.json", "{}")
        assert "ERROR" not in result

    def test_write_creates_parent_dirs(self, tmp_workspace):
        mod = _reload()
        mod.write_file("specs/sub/file.md", "data")
        assert (tmp_workspace / "specs" / "sub" / "file.md").exists()


class TestWriteSourceFile:
    def test_write_source_path(self, tmp_workspace):
        mod = _reload()
        result = mod.write_source_file("src/main.py", "print('hello')")
        assert (tmp_workspace / "src" / "main.py").read_text() == "print('hello')"
        assert "[SOURCE]" in result

    def test_write_rejects_artifact_path(self, tmp_workspace):
        mod = _reload()
        result = mod.write_source_file("specs/PROJ-1.md", "content")
        assert result.startswith("ERROR")
        assert not (tmp_workspace / "specs" / "PROJ-1.md").exists()

    def test_write_nested_source(self, tmp_workspace):
        mod = _reload()
        result = mod.write_source_file("app/services/user.py", "class User: pass")
        assert "ERROR" not in result
        assert (tmp_workspace / "app" / "services" / "user.py").exists()


class TestAppendFile:
    def test_append_to_artifact(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / ".morai").mkdir()
        (tmp_workspace / ".morai" / "log.md").write_text("line1\n")
        mod.append_file(".morai/log.md", "line2\n")
        assert (tmp_workspace / ".morai" / "log.md").read_text() == "line1\nline2\n"

    def test_append_creates_artifact_if_missing(self, tmp_workspace):
        mod = _reload()
        mod.append_file("specs/notes.md", "content")
        assert (tmp_workspace / "specs" / "notes.md").read_text() == "content"

    def test_append_rejects_source_path(self, tmp_workspace):
        mod = _reload()
        result = mod.append_file("src/config.py", "# config")
        assert result.startswith("ERROR")


class TestDeleteFile:
    def test_delete_existing(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / "del.txt").write_text("bye")
        result = mod.delete_file("del.txt")
        assert not (tmp_workspace / "del.txt").exists()
        assert "xóa" in result.lower() or "del.txt" in result

    def test_delete_missing_returns_message(self, tmp_workspace):
        mod = _reload()
        result = mod.delete_file("ghost.txt")
        assert "không tồn tại" in result.lower() or "ghost.txt" in result


class TestMoveFile:
    def test_move_renames_file(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / "old.txt").write_text("data")
        mod.move_file("old.txt", "new.txt")
        assert not (tmp_workspace / "old.txt").exists()
        assert (tmp_workspace / "new.txt").read_text() == "data"

    def test_move_missing_returns_message(self, tmp_workspace):
        mod = _reload()
        result = mod.move_file("ghost.txt", "dest.txt")
        assert "không tồn tại" in result.lower() or "ghost.txt" in result


class TestPathTraversal:
    def test_traversal_blocked(self, tmp_workspace):
        mod = _reload()
        with pytest.raises(ValueError, match="ngoài workspace"):
            mod.read_file("../../../etc/passwd")


class TestListFiles:
    def test_list_returns_files(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / "a.py").write_text("")
        (tmp_workspace / "b.py").write_text("")
        files = mod.list_files(".", "*.py")
        assert any("a.py" in f for f in files)
        assert any("b.py" in f for f in files)


class TestFileExists:
    def test_exists_true(self, tmp_workspace):
        mod = _reload()
        (tmp_workspace / "exists.txt").write_text("")
        assert mod.file_exists("exists.txt") is True

    def test_exists_false(self, tmp_workspace):
        mod = _reload()
        assert mod.file_exists("nope.txt") is False
