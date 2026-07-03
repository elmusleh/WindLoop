#!/usr/bin/env bash
# Run tests with coverage reporting
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if command -v pytest &> /dev/null && python3 -c "import pytest_cov" 2>/dev/null; then
    echo "Running pytest with coverage..."
    pytest tests/ --cov=src --cov-report=term-missing -v
else
    echo "pytest-cov not installed. Running tests without coverage."
    echo "Install with: pip install pytest-cov"
    pytest tests/ -v
fi
