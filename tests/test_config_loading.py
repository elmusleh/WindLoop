#!/usr/bin/env python3
"""Test config loading: --config, --profile, mutual exclusion."""

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


def test_list_profiles():
    print("[1/5] Testing --list-profiles...")
    result = run_with_args(["--list-profiles"])
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "quick-test" in result.stdout or "bug-fix" in result.stdout, "No profiles listed"
    print("  PASS")


def test_config_loading():
    print("[2/5] Testing --config with valid file...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("iterations: 2\nwindow_title: Windsurf\n")
        temp_path = f.name

    result = run_with_args(["--config", temp_path, "--list-profiles"])
    # --config doesn't affect --list-profiles, but it should not crash
    assert result.returncode == 0, f"Failed: {result.stderr}"
    Path(temp_path).unlink()
    print("  PASS")


def test_config_not_found():
    print("[3/5] Testing --config with missing file...")
    result = run_with_args(["--config", "/nonexistent/config.yaml"])
    assert result.returncode == 1, "Should exit with code 1"
    assert "not found" in result.stdout or "not found" in result.stderr
    print("  PASS")


def test_mutual_exclusion():
    print("[4/5] Testing --config + --profile mutual exclusion...")
    result = run_with_args(["--config", "/tmp/test.yaml", "--profile", "quick-test"])
    assert result.returncode == 1, "Should exit with code 1"
    assert "mutually exclusive" in (result.stdout + result.stderr)
    print("  PASS")


def test_profile_loading():
    print("[5/5] Testing --profile with known profile...")
    result = run_with_args(["--profile", "quick-test", "--list-profiles"])
    assert result.returncode == 0, f"Failed: {result.stderr}"
    print("  PASS")


if __name__ == "__main__":
    test_list_profiles()
    test_config_loading()
    test_config_not_found()
    test_mutual_exclusion()
    test_profile_loading()
    print("\nAll config loading tests passed.")
