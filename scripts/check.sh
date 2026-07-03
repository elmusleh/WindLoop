#!/usr/bin/env bash
# Pre-commit / pre-push syntax gate for cascade-loop
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ERRORS=0

echo "[1/4] Checking Python syntax..."
if python3 -m py_compile "$PROJECT_ROOT/src/cascade_loop.py"; then
    echo "  PASS: src/cascade_loop.py"
else
    echo "  FAIL: src/cascade_loop.py"
    ERRORS=$((ERRORS + 1))
fi

echo "[2/4] Checking bash scripts..."
for script in "$PROJECT_ROOT/bin/cascade-loop" "$PROJECT_ROOT/bin/cascade-loop-daemon" "$PROJECT_ROOT/install.sh"; do
    if command -v shellcheck &> /dev/null; then
        if shellcheck "$script"; then
            echo "  PASS: $(basename "$script")"
        else
            echo "  FAIL: $(basename "$script")"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "  SKIP: shellcheck not installed — run 'sudo apt-get install shellcheck'"
    fi
done

echo "[3/4] Checking YAML config..."
if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/config/config.yaml'))"; then
    echo "  PASS: config.yaml"
else
    echo "  FAIL: config.yaml"
    ERRORS=$((ERRORS + 1))
fi

echo "[4/4] Running Python tests..."
for test_file in "$PROJECT_ROOT"/tests/test_*.py; do
    if [ -f "$test_file" ]; then
        basename_tf=$(basename "$test_file")
        # Skip test_focus.py if Windsurf is not running
        if [ "$basename_tf" = "test_focus.py" ]; then
            if ! xdotool search --name "Windsurf" > /dev/null 2>&1; then
                echo "  SKIP: $basename_tf (Windsurf not running)"
                continue
            fi
        fi
        if python3 "$test_file"; then
            echo "  PASS: $basename_tf"
        else
            echo "  FAIL: $basename_tf"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ "$ERRORS" -eq 0 ]; then
    echo ""
    echo "All checks passed."
    exit 0
else
    echo ""
    echo "$ERRORS check(s) failed. Fix before committing."
    exit 1
fi
