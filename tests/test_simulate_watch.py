#!/usr/bin/env python3
"""Automated test: verify --simulate produces valid data for --watch."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src" / "cascade_loop.py"
JSON_LOG = PROJECT_ROOT / "logs" / "iterations.json"

EXPECTED_STATUSES = {"done", "timeout", "dry-run"}
REQUIRED_FIELDS = {"iteration", "status", "start_time", "end_time", "duration_sec", "error", "files_modified"}


def run_simulate():
    print("[1/4] Running cascade-loop --simulate...")
    result = subprocess.run(
        ["python3", str(SRC), "--simulate"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"FAIL: --simulate failed:\n{result.stderr}")
        sys.exit(1)
    print("  PASS")


def check_json_exists():
    print("[2/4] Checking iterations.json exists...")
    if not JSON_LOG.exists():
        print(f"FAIL: {JSON_LOG} not found")
        sys.exit(1)
    print("  PASS")


def validate_records():
    print("[3/4] Validating records...")
    with open(JSON_LOG) as f:
        records = json.load(f)

    if len(records) != 5:
        print(f"FAIL: Expected 5 records, got {len(records)}")
        sys.exit(1)

    seen_iterations = set()
    for r in records:
        # Check required fields
        missing = REQUIRED_FIELDS - set(r.keys())
        if missing:
            print(f"FAIL: Record missing fields: {missing}")
            sys.exit(1)

        # Check status is valid
        if r["status"] not in EXPECTED_STATUSES:
            print(f"FAIL: Invalid status '{r['status']}'")
            sys.exit(1)

        # Check iteration uniqueness
        if r["iteration"] in seen_iterations:
            print(f"FAIL: Duplicate iteration {r['iteration']}")
            sys.exit(1)
        seen_iterations.add(r["iteration"])

        # Check duration is non-negative
        if r["duration_sec"] < 0:
            print(f"FAIL: Negative duration: {r['duration_sec']}")
            sys.exit(1)

        # Check files_modified is a list
        if not isinstance(r["files_modified"], list):
            print(f"FAIL: files_modified is not a list")
            sys.exit(1)

    print("  PASS")


def check_specific_data():
    print("[4/4] Checking expected data patterns...")
    with open(JSON_LOG) as f:
        records = json.load(f)

    # Should have at least one done, one timeout, one dry-run
    statuses = {r["status"] for r in records}
    for expected in {"done", "timeout", "dry-run"}:
        if expected not in statuses:
            print(f"FAIL: Missing expected status '{expected}'")
            sys.exit(1)

    # The timeout record should have an error
    timeout_records = [r for r in records if r["status"] == "timeout"]
    if not timeout_records or not timeout_records[0].get("error"):
        print("FAIL: Timeout record should have an error field set")
        sys.exit(1)

    print("  PASS")


if __name__ == "__main__":
    run_simulate()
    check_json_exists()
    validate_records()
    check_specific_data()
    print("\nAll tests passed.")
