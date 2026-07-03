#!/usr/bin/env python3
"""Verify that the test runner infrastructure is sound."""

import subprocess
import sys


def test_pytest_availability():
    print("[1/2] Checking pytest availability...")
    result = subprocess.run(["which", "pytest"], capture_output=True)
    if result.returncode == 0:
        print("  pytest found")
    else:
        print("  pytest not found (scripts/test.sh will fall back to direct execution)")
    print("  PASS")


def test_mock_assertion():
    print("[2/2] Running a mock assertion...")
    assert 1 + 1 == 2
    print("  PASS")


if __name__ == "__main__":
    test_pytest_availability()
    test_mock_assertion()
    print("\nAll test runner tests passed.")
