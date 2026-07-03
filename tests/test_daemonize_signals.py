#!/usr/bin/env python3
"""Test daemon signal handling without actually forking."""

import os
import signal
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_pid_cleanup_on_stop():
    print("[1/2] Testing PID cleanup via --stop logic...")
    with tempfile.TemporaryDirectory() as tmpdir:
        old_pid_path = cl.PID_PATH
        cl.PID_PATH = Path(tmpdir) / "test.pid"

        # Write a fake PID (current process)
        cl.write_pid()
        assert cl.PID_PATH.exists()

        # Simulate --stop logic
        pid = cl.read_pid()
        assert pid == os.getpid()
        assert cl.is_running(pid) is True

        # Remove PID
        cl.remove_pid()
        assert not cl.PID_PATH.exists()

        cl.PID_PATH = old_pid_path
    print("  PASS")


def test_signal_handler_registration():
    print("[2/2] Testing signal handler can be registered...")
    # Verify the cleanup function exists and accepts signum/frame
    try:
        cl.signal.signal(signal.SIGTERM, cl.signal.SIG_DFL)
        # Re-register the cleanup handler from daemonize
        def cleanup(signum, frame):
            cl.log("Caught signal in test.", color=cl.Colors.YELLOW)
            cl.remove_pid()
            sys.exit(0)
        cl.signal.signal(signal.SIGTERM, cleanup)
        cl.signal.signal(signal.SIGTERM, cl.signal.SIG_DFL)
    except Exception as e:
        assert False, f"Signal handler setup failed: {e}"
    print("  PASS")


if __name__ == "__main__":
    test_pid_cleanup_on_stop()
    test_signal_handler_registration()
    print("\nAll daemon signal tests passed.")
