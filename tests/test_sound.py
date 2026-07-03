#!/usr/bin/env python3
"""Test sound playback function."""

import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_play_sound_no_file():
    print("[1/2] Testing play_sound() with no file (terminal bell)...")
    # Should not raise an error even if no audio subsystem exists
    cl.play_sound()
    print("  PASS")


def test_play_sound_custom_file_missing():
    print("[2/2] Testing play_sound() with missing custom file...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        cl.play_sound("/nonexistent/file.wav")
    print("  PASS")


if __name__ == "__main__":
    test_play_sound_no_file()
    test_play_sound_custom_file_missing()
    print("\nAll sound tests passed.")
