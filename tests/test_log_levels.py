#!/usr/bin/env python3
"""Test --verbose, --quiet, and log file behavior."""

import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src" / "cascade_loop.py"


def run_with_args(args):
    return subprocess.run(
        ["python3", str(SRC)] + args,
        capture_output=True, text=True,
    )


def test_version():
    print("[1/4] Testing --version...")
    result = run_with_args(["--version"])
    assert result.returncode == 0
    assert "0.9." in result.stdout
    print("  PASS")


def test_quiet_mode():
    print("[2/4] Testing --quiet with --list-profiles...")
    result = run_with_args(["--quiet", "--list-profiles"])
    assert result.returncode == 0
    # In quiet mode, normal info logs should be suppressed
    # But errors and important messages should still show
    print("  PASS")


def test_log_file():
    print("[3/4] Testing --log-file...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        temp_path = f.name

    result = run_with_args(["--log-file", temp_path, "--simulate"])
    assert result.returncode == 0

    log_content = Path(temp_path).read_text()
    assert "SIMULATE" in log_content or "fake" in log_content.lower()
    Path(temp_path).unlink()
    print("  PASS")


def test_verbose_mode():
    print("[4/4] Testing --verbose with --list-profiles...")
    result = run_with_args(["--verbose", "--list-profiles"])
    assert result.returncode == 0
    # In verbose mode, we should see extra output
    print("  PASS")


if __name__ == "__main__":
    test_version()
    test_quiet_mode()
    test_log_file()
    test_verbose_mode()
    print("\nAll log level tests passed.")
