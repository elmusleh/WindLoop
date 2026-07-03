#!/usr/bin/env python3
"""Test --health-check mode with mocked dependencies."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_health_check_all_present():
    print("[1/2] Testing --health-check with all deps present...")
    with patch("subprocess.run") as mock_run:
        def side_effect(cmd, **kwargs):
            m = MagicMock()
            m.returncode = 0
            if cmd[0] == "which" and cmd[1] in ("xdotool", "wmctrl", "inotifywait", "notify-send", "paplay"):
                m.returncode = 0
            elif cmd[0] == "xdotool" and cmd[1] == "search":
                m.returncode = 0
                m.stdout = b"12345\n"
            return m
        mock_run.side_effect = side_effect

        try:
            cl.health_check_mode()
        except SystemExit as e:
            assert e.code == 0, f"Expected exit 0, got {e.code}"
    print("  PASS")


def test_health_check_missing_critical():
    print("[2/2] Testing --health-check with missing critical dep...")
    with patch("subprocess.run") as mock_run:
        def side_effect(cmd, **kwargs):
            m = MagicMock()
            m.returncode = 1
            if cmd[0] == "xdotool" and cmd[1] == "search":
                m.returncode = 1
            return m
        mock_run.side_effect = side_effect

        try:
            cl.health_check_mode()
        except SystemExit as e:
            assert e.code == 1, f"Expected exit 1, got {e.code}"
    print("  PASS")


if __name__ == "__main__":
    test_health_check_all_present()
    test_health_check_missing_critical()
    print("\nAll health-check tests passed.")
