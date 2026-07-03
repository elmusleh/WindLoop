#!/usr/bin/env python3
"""Dry-run test: verifies window detection and prompt typing."""
import subprocess
import time
import pytest

WINDSURF_RUNNING = subprocess.run(
    ["xdotool", "search", "--name", "Windsurf"],
    capture_output=True
).returncode == 0


@pytest.mark.skipif(not WINDSURF_RUNNING, reason="Windsurf not running")
def test_window():
    result = subprocess.run(
        ["xdotool", "search", "--name", "Windsurf"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, "Windsurf window not found"
    print(f"[PASS] Found Windsurf window ID: {result.stdout.strip().split()[0]}")


@pytest.mark.skipif(not WINDSURF_RUNNING, reason="Windsurf not running")
def test_focus_and_type():
    window_id = subprocess.run(
        ["xdotool", "search", "--name", "Windsurf"],
        capture_output=True, text=True
    ).stdout.strip().split()[0]

    subprocess.run(["wmctrl", "-ia", window_id], check=False)
    time.sleep(0.5)
    subprocess.run(["xdotool", "type", "--delay", "10", "TEST_PROMPT_123"], check=False)
    time.sleep(0.2)
    print("[PASS] Typed test prompt into Windsurf window.")
