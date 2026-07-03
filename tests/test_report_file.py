#!/usr/bin/env python3
"""Test --report-file end-to-end."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_report_file():
    print("[1/1] Testing write_report_file() end-to-end...")
    # Ensure we have data first
    subprocess.run(
        ["python3", str(PROJECT_ROOT / "src" / "cascade_loop.py"), "--simulate"],
        capture_output=True, text=True,
    )

    report_path = Path("/tmp/cascade-test-report.html")
    if report_path.exists():
        report_path.unlink()

    cl.write_report_file(str(report_path))
    assert report_path.exists(), f"Report file not created: {report_path}"
    html = report_path.read_text()
    assert "<html>" in html
    assert "<table>" in html
    assert "Iteration Report" in html

    report_path.unlink()
    print("  PASS")


if __name__ == "__main__":
    test_report_file()
    print("\nAll report-file tests passed.")
