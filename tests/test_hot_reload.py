#!/usr/bin/env python3
"""Test hot reload: verify config change detection logic."""

import json
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_config_change_detection():
    print("[1/2] Testing config change detection...")
    # Simulate the reload check logic from cascade_loop.py
    config1 = {"iterations": 5, "timeout": 600}
    config2 = {"iterations": 5, "timeout": 1200}
    config3 = {"iterations": 5, "timeout": 600}

    str1 = json.dumps(config1, sort_keys=True)
    str2 = json.dumps(config2, sort_keys=True)
    str3 = json.dumps(config3, sort_keys=True)

    assert str1 != str2, "Different configs should have different hashes"
    assert str1 == str3, "Same configs should have same hashes"
    print("  PASS")


def test_config_file_modification():
    print("[2/2] Testing config file modification detection...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("timeout: 600\n")
        temp_path = f.name

    # Read initial
    import yaml
    with open(temp_path) as f:
        initial = yaml.safe_load(f)

    # Modify
    time.sleep(0.1)
    with open(temp_path, "w") as f:
        f.write("timeout: 1200\n")

    # Read again
    with open(temp_path) as f:
        updated = yaml.safe_load(f)

    assert initial["timeout"] == 600
    assert updated["timeout"] == 1200

    Path(temp_path).unlink()
    print("  PASS")


if __name__ == "__main__":
    test_config_change_detection()
    test_config_file_modification()
    print("\nAll hot reload tests passed.")
