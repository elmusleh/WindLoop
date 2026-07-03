#!/usr/bin/env python3
"""Test --config-init functionality."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl

CONFIG_PATH = cl.DEFAULT_CONFIG_PATH
ORIGINAL_CONFIG = None


def _backup():
    global ORIGINAL_CONFIG
    if CONFIG_PATH.exists():
        ORIGINAL_CONFIG = CONFIG_PATH.read_text()
    else:
        ORIGINAL_CONFIG = None


def _restore():
    if ORIGINAL_CONFIG is not None:
        CONFIG_PATH.write_text(ORIGINAL_CONFIG)
    elif CONFIG_PATH.exists():
        CONFIG_PATH.unlink()


def test_config_init_creates_file():
    print("[1/4] Testing init_config_mode creates config...")
    _backup()
    try:
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
        cl.init_config_mode(force=False)
        assert CONFIG_PATH.exists(), f"Config not created: {CONFIG_PATH}"
        text = CONFIG_PATH.read_text()
        assert "prompt_template" in text
        assert "ITERATION_DONE" in text
        assert "window_title" in text
    finally:
        _restore()
    print("  PASS")


def test_config_init_refuses_overwrite():
    print("[2/4] Testing init_config_mode refuses overwrite without force...")
    _backup()
    try:
        if not CONFIG_PATH.exists():
            cl.init_config_mode(force=False)
        try:
            cl.init_config_mode(force=False)
            assert False, "Should have exited with error"
        except SystemExit as e:
            assert e.code == 1, f"Expected exit 1, got {e.code}"
    finally:
        _restore()
    print("  PASS")


def test_config_init_force_overwrite():
    print("[3/4] Testing init_config_mode overwrites with force...")
    _backup()
    try:
        if not CONFIG_PATH.exists():
            cl.init_config_mode(force=False)
        cl.init_config_mode(force=True)
        assert CONFIG_PATH.exists()
    finally:
        _restore()
    print("  PASS")


def test_config_init_generates_valid_config():
    print("[4/4] Testing generated config passes validation...")
    _backup()
    try:
        if not CONFIG_PATH.exists():
            cl.init_config_mode(force=False)
        cl.validate_config_mode(str(CONFIG_PATH))
    except SystemExit as e:
        assert e.code == 0, f"Generated config should be valid, got exit {e.code}"
    finally:
        _restore()
    print("  PASS")


if __name__ == "__main__":
    test_config_init_creates_file()
    test_config_init_refuses_overwrite()
    test_config_init_force_overwrite()
    test_config_init_generates_valid_config()
    print("\nAll config-init tests passed.")
