#!/usr/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$PROJECT_ROOT/src/cascade_loop.py"
BIN="$PROJECT_ROOT/bin"

# Read version from source
VERSION=$(grep "__version__" "$SRC" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')

echo "=========================================="
echo "  Cascade Loop Installer"
echo "  Version: $VERSION"
echo "=========================================="

# Parse args
CHECK_ONLY=false
if [[ "${1:-}" == "--check" || "${1:-}" == "-c" ]]; then
    CHECK_ONLY=true
    echo "Running dependency check only..."
fi

# Dependency checks
deps_ok=true
for cmd in python3 xdotool wmctrl inotifywait; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  [OK]   $cmd"
    else
        echo "  [MISSING] $cmd"
        deps_ok=false
    fi
done

if ! $deps_ok; then
    echo ""
    echo "Install missing dependencies:"
    echo "  sudo apt-get install xdotool wmctrl inotify-tools python3-yaml"
    exit 1
fi

# Python package check
if python3 -c "import yaml" 2>/dev/null; then
    echo "  [OK]   python3-yaml (PyYAML)"
else
    echo "  [MISSING] python3-yaml (PyYAML)"
    echo "Install: pip install pyyaml"
    exit 1
fi

if $CHECK_ONLY; then
    echo ""
    echo "All dependencies satisfied."
    exit 0
fi

# Create bin directory and symlinks
mkdir -p "$BIN"

if [[ ! -L "$BIN/cascade-loop" ]]; then
    ln -s "$SRC" "$BIN/cascade-loop"
    echo "Created bin/cascade-loop"
fi

if [[ ! -L "$BIN/cascade-loop-daemon" ]]; then
    cat > "$BIN/cascade-loop-daemon" << 'DAEMON'
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if pgrep -f "cascade_loop.py --daemon" > /dev/null; then
    "$PROJECT_ROOT/bin/cascade-loop" --stop
else
    "$PROJECT_ROOT/bin/cascade-loop" --daemon
fi
DAEMON
    chmod +x "$BIN/cascade-loop-daemon"
    echo "Created bin/cascade-loop-daemon"
fi

# Install systemd service if systemd is available
if command -v systemctl >/dev/null 2>&1; then
    SERVICE_SRC="$PROJECT_ROOT/systemd/cascade-loop.service"
    SERVICE_DST="$HOME/.config/systemd/user/cascade-loop.service"
    if [[ -f "$SERVICE_SRC" && ! -f "$SERVICE_DST" ]]; then
        mkdir -p "$HOME/.config/systemd/user"
        cp "$SERVICE_SRC" "$SERVICE_DST"
        systemctl --user daemon-reload
        echo "Installed user systemd service"
    fi
fi

echo ""
echo "Installation complete (v$VERSION)."
echo "Usage: cascade-loop --start"
