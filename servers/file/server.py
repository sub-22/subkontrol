"""File MCP server — read/write files trong workspace.

Zone model:
  ARTIFACT zone: specs/, plans/, designs/, docs/, reviews/, tests/, tasks/,
                 incidents/, .morai/ — writable by most skills via write_file()
  SOURCE zone:   everything else (application source code) — writable ONLY
                 by dev skills via write_source_file()
"""

import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-file")

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))

# Directories considered "artifact zone" — non-source Morai outputs
ARTIFACT_DIRS = frozenset({
    "specs", "plans", "designs", "docs", "reviews",
    "tests", "tasks", "incidents", ".morai",
})


def _safe_path(relative_path: str) -> Path:
    """Đảm bảo path nằm trong WORKSPACE_ROOT."""
    target = (WORKSPACE_ROOT / relative_path).resolve()
    if not target.is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError(f"Path '{relative_path}' nằm ngoài workspace")
    return target


def _is_artifact_path(path: str) -> bool:
    """Returns True nếu path nằm trong artifact zone."""
    parts = Path(path).parts
    return bool(parts) and parts[0] in ARTIFACT_DIRS


@mcp.tool()
def read_file(path: str) -> str:
    """Đọc nội dung file (source hoặc artifact).

    Args:
        path: Relative path từ workspace root
    Returns:
        File content hoặc error message nếu không tìm thấy
    """
    target = _safe_path(path)
    if not target.exists():
        return f"ERROR: File không tồn tại: {path}"
    if not target.is_file():
        return f"ERROR: Không phải file: {path}"
    try:
        return target.read_text(encoding="utf-8")
    except OSError as e:
        return f"ERROR: Không đọc được file {path}: {e}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Ghi artifact file (specs, plans, reviews, designs, v.v.).

    Chỉ dùng cho ARTIFACT zone: specs/, plans/, designs/, docs/,
    reviews/, tests/, tasks/, incidents/, .morai/

    Để ghi source code, dùng write_source_file() — chỉ dev skills được phép.

    Args:
        path: Relative path từ workspace root (phải trong artifact zone)
        content: Nội dung cần ghi
    Returns:
        Thông báo thành công hoặc error
    """
    if not _is_artifact_path(path):
        return (
            f"ERROR: '{path}' nằm trong source zone. "
            f"Dùng write_source_file() để ghi source code (chỉ dev skills)."
        )
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Đã ghi: {path}"


@mcp.tool()
def write_source_file(path: str, content: str) -> str:
    """Ghi source code file — CHỈ dev skills được phép gọi tool này.

    Dùng cho application source code nằm ngoài artifact directories.
    Mỗi lần gọi được log riêng để audit.

    Args:
        path: Relative path từ workspace root (phải NGOÀI artifact zone)
        content: Nội dung cần ghi
    Returns:
        Thông báo thành công hoặc error
    """
    if _is_artifact_path(path):
        return (
            f"ERROR: '{path}' nằm trong artifact zone. "
            f"Dùng write_file() để ghi artifacts."
        )
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"[SOURCE] Đã ghi: {path}"


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
def append_file(path: str, content: str) -> str:
    """Append nội dung vào cuối file artifact, tạo file nếu chưa có.

    Chỉ dùng cho artifact zone. Dùng write_source_file() để sửa source code.

    Args:
        path: Relative path từ workspace root
        content: Nội dung cần append
    """
    if not _is_artifact_path(path):
        return (
            f"ERROR: '{path}' nằm trong source zone. "
            f"Dùng write_source_file() để ghi source code."
        )
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(content)
    return f"Đã append vào: {path}"


@mcp.tool()
def delete_file(path: str) -> str:
    """Xóa một file.

    Args:
        path: Relative path từ workspace root
    Returns:
        Kết quả hoặc error message
    """
    target = _safe_path(path)
    if not target.exists():
        return f"File không tồn tại: {path}"
    if not target.is_file():
        return f"Không phải file: {path}"
    target.unlink()
    return f"Đã xóa: {path}"


@mcp.tool()
def move_file(source: str, destination: str) -> str:
    """Di chuyển / đổi tên file.

    Args:
        source: Relative path nguồn
        destination: Relative path đích
    """
    src = _safe_path(source)
    dst = _safe_path(destination)
    if not src.exists():
        return f"File nguồn không tồn tại: {source}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return f"Đã move: {source} → {destination}"


@mcp.tool()
def file_exists(path: str) -> bool:
    """Kiểm tra file có tồn tại không.

    Args:
        path: Relative path từ workspace root
    """
    return _safe_path(path).exists()


if __name__ == "__main__":
    mcp.run()
