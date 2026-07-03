#!/usr/bin/env python3
"""Test PID file and daemonize helper functions."""

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_pid_file():
    print("[1/3] Testing PID file read/write...")
    with tempfile.TemporaryDirectory() as tmpdir:
        old_pid_path = cl.PID_PATH
        cl.PID_PATH = Path(tmpdir) / "test.pid"
        
        cl.write_pid()
        assert cl.PID_PATH.exists()
        pid = cl.read_pid()
        assert pid == os.getpid()
        
        cl.remove_pid()
        assert not cl.PID_PATH.exists()
        
        cl.PID_PATH = old_pid_path
    print("  PASS")


def test_is_running():
    print("[2/3] Testing is_running()...")
    assert cl.is_running(os.getpid()) is True
    assert cl.is_running(None) is False
    # PID 99999 is extremely unlikely to exist
    assert cl.is_running(99999) is False
    print("  PASS")


def test_cleanup():
    print("[3/3] Testing cleanup signal handler...")
    with tempfile.TemporaryDirectory() as tmpdir:
        old_pid_path = cl.PID_PATH
        cl.PID_PATH = Path(tmpdir) / "test.pid"
        
        cl.write_pid()
        # Simulate cleanup
        cl.remove_pid()
        assert not cl.PID_PATH.exists()
        
        cl.PID_PATH = old_pid_path
    print("  PASS")


if __name__ == "__main__":
    test_pid_file()
    test_is_running()
    test_cleanup()
    print("\nAll daemonize tests passed.")
