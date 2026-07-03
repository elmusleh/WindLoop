#!/usr/bin/env bash
# Install git hooks for this repository
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Installing git hooks..."
git config core.hooksPath .githooks
echo "Hooks installed from .githooks/"
echo "Run 'git config --unset core.hooksPath' to uninstall."
