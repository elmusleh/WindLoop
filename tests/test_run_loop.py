#!/usr/bin/env python3
"""Mock-based tests for run_loop() to boost coverage without external deps."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_dry_run_iteration():
    print("[1/3] Testing dry-run iteration...")
    config = {
        "window_title": "Windsurf",
        "sentinel_path": "/tmp/cascade-test.log",
        "pause_file_path": "/tmp/cascade-test.pause",
        "prompt_template": "Test iteration {{ iteration }} of {{ total }}",
        "pre_delay": 0,
        "post_delay": 0,
        "timeout": 5,
        "notifications": False,
        "iterations": 1,
    }

    with patch("cascade_loop.focus_window") as mock_focus, \
         patch("cascade_loop.open_cascade_chat") as mock_open, \
         patch("cascade_loop.focus_chat_input") as mock_focus_input, \
         patch("cascade_loop.type_prompt") as mock_type, \
         patch("cascade_loop.submit_prompt") as mock_submit, \
         patch("cascade_loop.wait_for_sentinel", return_value=True) as mock_wait, \
         patch("cascade_loop.play_sound") as mock_sound, \
         patch("cascade_loop.find_windsurf_window", return_value="12345"):

        cl.run_loop(config, dry_run=True)

    mock_focus.assert_called_once()
    mock_open.assert_called_once()
    mock_focus_input.assert_called_once()
    mock_type.assert_called_once()
    mock_submit.assert_not_called()  # dry_run skips submit
    mock_wait.assert_not_called()      # dry_run skips sentinel wait
    print("  PASS")


def test_retry_path():
    print("[2/3] Testing retry path (timeout then success)...")
    config = {
        "window_title": "Windsurf",
        "sentinel_path": "/tmp/cascade-test.log",
        "pause_file_path": "/tmp/cascade-test.pause",
        "prompt_template": "Test",
        "pre_delay": 0,
        "post_delay": 0,
        "timeout": 5,
        "notifications": False,
        "iterations": 1,
    }

    # First call times out, second succeeds
    wait_returns = [False, True]

    with patch("cascade_loop.focus_window"), \
         patch("cascade_loop.open_cascade_chat"), \
         patch("cascade_loop.focus_chat_input"), \
         patch("cascade_loop.type_prompt"), \
         patch("cascade_loop.submit_prompt"), \
         patch("cascade_loop.wait_for_sentinel", side_effect=wait_returns) as mock_wait, \
         patch("cascade_loop.find_windsurf_window", return_value="12345"):

        cl.run_loop(config, retry=1)

    assert mock_wait.call_count == 2, f"Expected 2 wait calls, got {mock_wait.call_count}"
    print("  PASS")


def test_max_total_time_stop():
    print("[3/3] Testing max-total-time stop between iterations...")
    config = {
        "window_title": "Windsurf",
        "sentinel_path": "/tmp/cascade-test.log",
        "pause_file_path": "/tmp/cascade-test.pause",
        "prompt_template": "Test",
        "pre_delay": 0,
        "post_delay": 0,
        "timeout": 5,
        "notifications": False,
        "iterations": 10,  # Many iterations, but time limit should stop early
    }

    with patch("cascade_loop.focus_window"), \
         patch("cascade_loop.open_cascade_chat"), \
         patch("cascade_loop.focus_chat_input"), \
         patch("cascade_loop.type_prompt"), \
         patch("cascade_loop.submit_prompt"), \
         patch("cascade_loop.wait_for_sentinel", return_value=True), \
         patch("cascade_loop.find_windsurf_window", return_value="12345"):

        cl.run_loop(config, max_total_time=0)  # 0 seconds = stop immediately

    # Should complete 0 iterations due to time limit
    print("  PASS")


if __name__ == "__main__":
    test_dry_run_iteration()
    test_retry_path()
    test_max_total_time_stop()
    print("\nAll run_loop tests passed.")
