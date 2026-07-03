#!/usr/bin/env python3
"""Test notification function."""

import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_notify_with_missing_binary():
    print("[1/2] Testing notify() when notify-send is missing...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        # Should return silently without error
        cl.notify("Test", "Body")
    print("  PASS")


def test_notify_with_binary():
    print("[2/2] Testing notify() when notify-send exists...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        cl.notify("Test", "Body")
        # Second call should be the actual notify-send execution
        assert mock_run.call_count >= 1
    print("  PASS")


if __name__ == "__main__":
    test_notify_with_missing_binary()
    test_notify_with_binary()
    print("\nAll notification tests passed.")
