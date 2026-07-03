#!/usr/bin/env bash
# Unified test runner for cascade-loop
# Auto-detects pytest; falls back to running test files directly
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

ERRORS=0
PASSED=0
SKIPPED=0

if command -v pytest &> /dev/null; then
    echo "Running tests with pytest..."
    if pytest tests/ -v; then
        echo ""
        echo "All pytest tests passed."
        exit 0
    else
        echo ""
        echo "Pytest reported failures."
        exit 1
    fi
fi

echo "pytest not found. Running tests directly..."
for test_file in tests/test_*.py; do
    if [ -f "$test_file" ]; then
        basename_tf=$(basename "$test_file")
        # Skip test_focus.py if Windsurf is not running
        if [ "$basename_tf" = "test_focus.py" ]; then
            if ! xdotool search --name "Windsurf" > /dev/null 2>&1; then
                echo "  SKIP: $basename_tf (Windsurf not running)"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi
        fi
        if python3 "$test_file"; then
            echo "  PASS: $basename_tf"
            PASSED=$((PASSED + 1))
        else
            echo "  FAIL: $basename_tf"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

echo ""
echo "Results: $PASSED passed, $SKIPPED skipped, $ERRORS failed"

if [ "$ERRORS" -eq 0 ]; then
    echo "All tests passed."
    exit 0
else
    echo "$ERRORS test(s) failed."
    exit 1
fi
