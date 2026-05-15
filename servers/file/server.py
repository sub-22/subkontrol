"""File MCP server — read/write files trong workspace.

Zone model:
  ARTIFACT zone: specs/, plans/, designs/, docs/, reviews/, tests/, tasks/,
                 incidents/, .morai/ — writable by most skills via write_file()
  SOURCE zone:   everything else (application source code) — writable ONLY
                 by dev skills via write_source_file()
"""

import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-file")

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))

# Directories considered "artifact zone" — non-source Morai outputs
ARTIFACT_DIRS = frozenset(
    {
        "specs",
        "plans",
        "designs",
        "docs",
        "reviews",
        "tests",
        "tasks",
        "incidents",
        ".morai",
    }
)


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
        return f"ERROR: '{path}' nằm trong artifact zone. Dùng write_file() để ghi artifacts."
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
            f"ERROR: '{path}' nằm trong source zone. Dùng write_source_file() để ghi source code."
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


_EXCLUDE_DIRS = frozenset(
    {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "coverage",
        ".cache",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)


@mcp.tool()
def project_summary() -> str:
    """Trả về tổng quan project: tech stack, directory tree, file counts, entry points, git info.

    Dùng đầu session để orient nhanh vào codebase.
    """
    root = WORKSPACE_ROOT.resolve()
    sections: list[str] = [f"# Project summary: {root.name}\n"]

    # tech stack
    stack: list[str] = []
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for lib, label in [
                ("react", "React"),
                ("vue", "Vue"),
                ("svelte", "Svelte"),
                ("next", "Next.js"),
                ("vite", "Vite"),
                ("typescript", "TypeScript"),
                ("jest", "Jest"),
                ("vitest", "Vitest"),
            ]:
                if lib in deps:
                    stack.append(label)
            if not stack:
                stack.append("Node.js")
        except (json.JSONDecodeError, KeyError):
            stack.append("Node.js")

    for py_cfg in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"):
        if (root / py_cfg).exists():
            stack.append("Python")
            break

    if (root / "go.mod").exists():
        stack.append("Go")
    if (root / "Cargo.toml").exists():
        stack.append("Rust")
    if (root / "pom.xml").exists():
        stack.append("Java/Maven")

    sections.append("## Tech stack\n" + (", ".join(stack) if stack else "unknown") + "\n")

    # file counts by extension
    counts: dict[str, int] = defaultdict(int)
    for f in root.rglob("*"):
        if f.is_file() and not any(p in _EXCLUDE_DIRS for p in f.parts):
            counts[f.suffix or "(no ext)"] += 1

    top = sorted(counts.items(), key=lambda x: -x[1])[:10]
    sections.append(
        "## File counts (top extensions)\n" + "\n".join(f"  {ext:12} {n}" for ext, n in top) + "\n"
    )

    # directory tree (2 levels)
    tree: list[str] = [f"{root.name}/"]
    for entry in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name)):
        if entry.name.startswith(".") or entry.name in _EXCLUDE_DIRS:
            continue
        if entry.is_dir():
            children = sorted(
                p.name
                for p in entry.iterdir()
                if not p.name.startswith(".") and p.name not in _EXCLUDE_DIRS
            )
            tree.append(f"  {entry.name}/")
            for child in children[:6]:
                tree.append(f"    {child}")
            if len(children) > 6:
                tree.append(f"    … {len(children) - 6} more")
        else:
            tree.append(f"  {entry.name}")
    sections.append("## Directory tree\n```\n" + "\n".join(tree) + "\n```\n")

    # entry points
    candidates = [
        "main.py",
        "app.py",
        "index.py",
        "src/main.jsx",
        "src/main.tsx",
        "src/main.js",
        "src/App.jsx",
        "src/App.tsx",
        "src/index.js",
        "index.js",
        "index.ts",
        "server.js",
        "server.ts",
    ]
    found = [c for c in candidates if (root / c).exists()]
    if found:
        sections.append("## Entry points\n" + "\n".join(f"  {e}" for e in found) + "\n")

    # git info
    if (root / ".git").exists():
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            log = subprocess.check_output(
                ["git", "log", "--oneline", "-3"],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            sections.append(
                f"## Git\nbranch: {branch}\nrecent commits:\n"
                + "\n".join(f"  {line}" for line in log.splitlines())
                + "\n"
            )
        except Exception:
            pass

    return "\n".join(sections)


if __name__ == "__main__":
    mcp.run()
