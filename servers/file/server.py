"""File MCP server — read/write files trong workspace."""

import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-file")

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))


def _safe_path(relative_path: str) -> Path:
    """Đảm bảo path nằm trong WORKSPACE_ROOT."""
    target = (WORKSPACE_ROOT / relative_path).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT.resolve())):
        raise ValueError(f"Path '{relative_path}' nằm ngoài workspace")
    return target


@mcp.tool()
def read_file(path: str) -> str:
    """Đọc nội dung file.

    Args:
        path: Relative path từ workspace root
    """
    return _safe_path(path).read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Ghi nội dung vào file, tạo thư mục nếu chưa có.

    Args:
        path: Relative path từ workspace root
        content: Nội dung cần ghi
    """
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Đã ghi: {path}"


@mcp.tool()
def list_files(directory: str = ".", pattern: str = "**/*") -> list[str]:
    """Liệt kê files trong thư mục.

    Args:
        directory: Relative path tới thư mục
        pattern: Glob pattern, e.g. "**/*.py"
    """
    base = _safe_path(directory)
    return [str(p.relative_to(WORKSPACE_ROOT)) for p in base.glob(pattern) if p.is_file()]


@mcp.tool()
def file_exists(path: str) -> bool:
    """Kiểm tra file có tồn tại không.

    Args:
        path: Relative path từ workspace root
    """
    return _safe_path(path).exists()


if __name__ == "__main__":
    mcp.run()
