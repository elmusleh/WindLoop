#!/usr/bin/env python3
"""Mock-based tests for wait_for_sentinel()."""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_wait_for_sentinel_success():
    print("[1/3] Testing wait_for_sentinel success path...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        tmp.write("ITERATION_DONE\n")
        tmp.flush()
        sentinel_path = Path(tmp.name)

    # Mock inotifywait to return immediately (simulate file change)
    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0
    mock_proc.kill = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.readline = MagicMock(return_value=b"")
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.read = MagicMock(return_value=b"")

    with patch("subprocess.Popen", return_value=mock_proc):
        result = cl.wait_for_sentinel(sentinel_path, timeout_sec=5)

    assert result is True
    sentinel_path.unlink()
    print("  PASS")


def test_wait_for_sentinel_timeout():
    print("[2/3] Testing wait_for_sentinel timeout path...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        tmp.write("")
        tmp.flush()
        sentinel_path = Path(tmp.name)

    mock_proc = MagicMock()
    from subprocess import TimeoutExpired
    mock_proc.wait.side_effect = TimeoutExpired("inotifywait", 1)
    mock_proc.kill = MagicMock()
    mock_proc.stdout = MagicMock()
    mock_proc.stderr = MagicMock()

    with patch("subprocess.Popen", return_value=mock_proc):
        result = cl.wait_for_sentinel(sentinel_path, timeout_sec=1)

    assert result is False
    mock_proc.kill.assert_called_once()
    sentinel_path.unlink()
    print("  PASS")


def test_wait_for_sentinel_missing_inotifywait():
    print("[3/3] Testing wait_for_sentinel missing inotifywait...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        tmp.write("")
        tmp.flush()
        sentinel_path = Path(tmp.name)

    with patch("subprocess.Popen", side_effect=FileNotFoundError("inotifywait")):
        try:
            cl.wait_for_sentinel(sentinel_path, timeout_sec=5)
            assert False, "Expected SystemExit"
        except SystemExit as e:
            assert e.code == 1

    sentinel_path.unlink()
    print("  PASS")


if __name__ == "__main__":
    test_wait_for_sentinel_success()
    test_wait_for_sentinel_timeout()
    test_wait_for_sentinel_missing_inotifywait()
    print("\nAll sentinel tests passed.")
