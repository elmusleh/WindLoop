#!/usr/bin/env python3
"""Test --stats flag and stats_mode()."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src" / "cascade_loop.py"
JSON_LOG = PROJECT_ROOT / "logs" / "iterations.json"


def test_stats_empty():
    print("[1/3] Testing --stats with no data...")
    # Temporarily move existing log
    backup = None
    if JSON_LOG.exists():
        backup = JSON_LOG.read_text()
        JSON_LOG.unlink()
    
    result = subprocess.run(
        ["python3", str(SRC), "--stats"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "No iteration data" in result.stdout
    
    if backup:
        JSON_LOG.write_text(backup)
    print("  PASS")


def test_stats_with_data():
    print("[2/3] Testing --stats with fake data...")
    # Run simulate first to ensure data exists
    subprocess.run(
        ["python3", str(SRC), "--simulate"],
        capture_output=True, text=True,
    )
    
    result = subprocess.run(
        ["python3", str(SRC), "--stats"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Total iterations" in result.stdout
    assert "Successful" in result.stdout
    print("  PASS")


def test_stats_corrupted_json():
    print("[3/3] Testing --stats with corrupted JSON...")
    backup = None
    if JSON_LOG.exists():
        backup = JSON_LOG.read_text()
    
    JSON_LOG.write_text("not valid json{{{")
    
    result = subprocess.run(
        ["python3", str(SRC), "--stats"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "Cannot read" in result.stdout or "Cannot read" in result.stderr
    
    if backup:
        JSON_LOG.write_text(backup)
    else:
        JSON_LOG.unlink()
    print("  PASS")


if __name__ == "__main__":
    test_stats_empty()
    test_stats_with_data()
    test_stats_corrupted_json()
    print("\nAll stats tests passed.")
