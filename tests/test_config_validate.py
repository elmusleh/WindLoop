#!/usr/bin/env python3
"""Test --config-validate mode."""

import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_validate_valid_config():
    print("[1/3] Testing validate_config_mode with valid config...")
    # Use the actual project config
    config_path = str(PROJECT_ROOT / "config" / "config.yaml")
    try:
        cl.validate_config_mode(config_path)
    except SystemExit as e:
        assert e.code == 0, f"Expected exit 0, got {e.code}"
    print("  PASS")


def test_validate_missing_file():
    print("[2/3] Testing validate_config_mode with missing file...")
    try:
        cl.validate_config_mode("/nonexistent/config.yaml")
    except SystemExit as e:
        assert e.code == 1, f"Expected exit 1, got {e.code}"
    print("  PASS")


def test_validate_invalid_yaml():
    print("[3/3] Testing validate_config_mode with invalid YAML...")
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: [bad\n")
        tmp_path = f.name

    try:
        cl.validate_config_mode(tmp_path)
    except SystemExit as e:
        assert e.code == 1, f"Expected exit 1, got {e.code}"
    finally:
        os.unlink(tmp_path)
    print("  PASS")


if __name__ == "__main__":
    test_validate_valid_config()
    test_validate_missing_file()
    test_validate_invalid_yaml()
    print("\nAll config-validate tests passed.")
