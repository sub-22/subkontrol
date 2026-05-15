"""Test runner MCP server — chạy pytest, coverage, và detect test framework."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-test")

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))


@mcp.tool()
def run_pytest(
    paths: list[str] | None = None,
    timeout: int = 120,
    extra_args: list[str] | None = None,
) -> dict:
    """Chạy pytest và trả về structured report.

    Args:
        paths: Danh sách test files/dirs cụ thể (bỏ trống = chạy tất cả)
        timeout: Timeout tính bằng giây
        extra_args: Các flags bổ sung cho pytest (e.g. ["-k", "test_login"])
    Returns:
        {passed, failed, errors, skipped, duration, failed_tests}
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = tmp.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--json-report",
            f"--json-report-file={report_path}",
            "-q",
        ]
        if paths:
            cmd.extend(paths)
        if extra_args:
            cmd.extend(extra_args)

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_ROOT,
        )

        report = json.loads(Path(report_path).read_text())
    except FileNotFoundError:
        return {"error": "pytest hoặc pytest-json-report chưa được cài đặt"}
    except json.JSONDecodeError:
        return {"error": "Không parse được test report"}
    except subprocess.TimeoutExpired:
        return {"error": f"Test timeout sau {timeout}s"}
    finally:
        Path(report_path).unlink(missing_ok=True)

    summary = report.get("summary", {})
    failed_tests = [
        {
            "name": t["nodeid"],
            "error": t.get("call", {}).get("longrepr", ""),
        }
        for t in report.get("tests", [])
        if t.get("outcome") == "failed"
    ]

    return {
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "errors": summary.get("errors", 0),
        "skipped": summary.get("skipped", 0),
        "duration": round(report.get("duration", 0), 3),
        "failed_tests": failed_tests,
    }


@mcp.tool()
def run_coverage(
    paths: list[str] | None = None,
    timeout: int = 120,
) -> dict:
    """Chạy pytest với coverage report.

    Args:
        paths: Test files/dirs cụ thể (bỏ trống = tất cả)
        timeout: Timeout tính bằng giây
    Returns:
        {line_rate, lines_covered, lines_total} hoặc error
    """
    cmd = [sys.executable, "-m", "pytest", "--cov=.", "--cov-report=json", "-q"]
    if paths:
        cmd.extend(paths)

    subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=WORKSPACE_ROOT,
    )

    coverage_file = WORKSPACE_ROOT / "coverage.json"
    if not coverage_file.exists():
        return {"error": "coverage.json không được tạo — đã cài pytest-cov chưa?"}

    data = json.loads(coverage_file.read_text())
    totals = data.get("totals", {})
    return {
        "line_rate": round(totals.get("percent_covered", 0), 2),
        "lines_covered": totals.get("covered_lines", 0),
        "lines_total": totals.get("num_statements", 0),
    }


@mcp.tool()
def detect_test_framework(path: str | None = None) -> str:
    """Detect test framework đang dùng trong project.

    Returns:
        Một trong: pytest | unittest | jest | vitest | unknown
    """
    root = WORKSPACE_ROOT / path if path else WORKSPACE_ROOT

    for config_file in ("pyproject.toml", "setup.cfg", "pytest.ini", "tox.ini"):
        f = root / config_file
        if f.exists() and "pytest" in f.read_text(encoding="utf-8", errors="ignore"):
            return "pytest"

    if list(root.rglob("test_*.py")) or list(root.rglob("*_test.py")):
        return "pytest"

    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            combined = str(pkg.get("scripts", {})) + str(pkg.get("devDependencies", {}))
            if "vitest" in combined:
                return "vitest"
            if "jest" in combined:
                return "jest"
        except (json.JSONDecodeError, KeyError):
            pass

    return "unknown"


if __name__ == "__main__":
    mcp.run()
