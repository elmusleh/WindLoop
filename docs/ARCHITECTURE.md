# Architecture

## System Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Config    │────▶│   Python    │────▶│  Windsurf   │
│ config.yaml │     │  Script     │     │  Cascade    │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                     │
                           │    types prompt    │
                           │◄────────────────────│
                           │                     │
                           │   AI works, edits   │
                           │                     │
                           │  writes sentinel   │
                           │◄────────────────────│
                           │                     │
                    ┌──────┴──────┐              │
                    │ inotifywait │◄─────────────┘
                    │   blocks    │
                    └──────┬──────┘
                           │ wakes up
                           ▼
                    next iteration
```

## Sentinel Pattern

The sentinel is a file watched by `inotifywait`. When the AI appends `ITERATION_DONE`, the script unblocks and continues.

**Why this works:**
- AI generation time is unpredictable (5s to 10+ min)
- Fixed `sleep` would waste time or fail on long operations
- File-based signaling is robust and OS-native

## Window Automation Flow

1. `xdotool search --name "Windsurf"` → get window ID
2. `wmctrl -ia <id>` → focus window
3. `xdotool key ctrl+shift+p` → open command palette
4. `xdotool type "Open Cascade Chat"` → search command
5. `xdotool key Return` → execute
6. `xdotool type <prompt>` → enter prompt
7. `xdotool key Return` → submit

## Daemonization

Double-fork pattern:
- Fork 1: detach from parent, create new session
- Fork 2: prevent terminal acquisition, run in background
- PID file written to `~/.windsurf/cascade-loop.pid`

## Logging

```
logs/
├── iterations.log    # Human-readable per-iteration status
└── (future) iterations.json  # Structured data
```
