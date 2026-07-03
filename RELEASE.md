# Release Notes — cascade-loop v0.9.11

**Release Date:** 2026-06-17
**Tests:** 46 passing, 2 skipped | **Coverage:** ~33%

---

## Summary

cascade-loop is a Linux desktop automation tool that runs AI prompts in [Windsurf](https://www.codeium.com/windsurf) Cascade in a loop, detecting completion via a sentinel file (`ITERATION_DONE`). It provides robust control mechanisms including retry logic, time limits, live monitoring, notifications, and extensive CLI configurability.

---

## Features (32 CLI Flags)

| # | Feature | Flag | Description |
|---|---|---|---|
| 1 | Start Loop | `--start` | Run in foreground |
| 2 | Daemon Mode | `--daemon` | Run in background |
| 3 | Stop | `--stop` | Kill background loop |
| 4 | Status | `--status` | Show if running |
| 5 | Dry Run | `--dry-run` | Test without submitting |
| 6 | Live Monitor | `--watch` | Real-time iteration table |
| 7 | Simulate | `--simulate` | Generate fake test data |
| 8 | Profiles | `--profile` | Load YAML config profiles |
| 9 | List Profiles | `--list-profiles` | Show available profiles |
| 10 | Custom Config | `--config` | Use arbitrary YAML config |
| 11 | Config Validate | `--config-validate` | Check config without starting |
| 12 | Config Init | `--config-init` | Generate starter config |
| 13 | Window Index | `--window-index` | Target specific Windsurf window |
| 14 | Sound | `--sound` | Play completion tone |
| 15 | Custom Sound | `--sound-file` | Use custom audio file |
| 16 | Retry | `--retry` | Restart timed-out iterations |
| 17 | Time Limit | `--max-total-time` | Cap total runtime |
| 18 | No Focus | `--no-focus` | Skip window focusing |
| 19 | Verbose | `--verbose` | Debug output |
| 20 | Quiet | `--quiet` | Suppress non-essential output |
| 21 | Log File | `--log-file` | Redirect output to file |
| 22 | Version | `--version` | Show version |
| 23 | Statistics | `--stats` | Aggregate performance |
| 24 | Clear Stats | `--clear-stats` | Archive and reset history |
| 25 | Export | `--export-stats` | CSV / HTML reports |
| 26 | Health Check | `--health-check` | Validate dependencies |
| 27 | Benchmark | `--benchmark` | Per-step timing |
| 28 | Schedule | `--schedule` | Delayed start |
| 29 | Email Report | `--report` | Email HTML on completion |
| 30 | Report File | `--report-file` | Write HTML to custom path |
| 31 | Webhook | `--webhook` | POST JSON stats |
| 32 | Webhook Headers | `--webhook-headers` | Custom auth headers |

---

## Test Suite

- **46 tests** covering all major paths
- **2 skipped** (require Windsurf running)
- Mock-based tests for: sentinel, daemonize, signals, run_loop, health check, webhooks, webhook headers, report file, config validation, config init
- Syntax gate via `scripts/check.sh`
- CI via GitHub Actions (Python 3.11/3.12 matrix)

---

## Requirements

- Linux Mint (or any Linux with X11)
- Python 3.11+
- `xdotool`, `wmctrl`, `inotifywait`
- Windsurf with Auto-approve edits enabled

## Install

```bash
./install.sh --check   # validate deps
./install.sh           # full install
```

---

## Quick Start

```bash
cascade-loop --config-init       # generate starter config
cascade-loop --config-validate   # check it
cascade-loop --health-check      # verify environment
cascade-loop --start             # run the loop
```

---

## Roadmap to v1.0.0

- [x] All planned CLI features implemented
- [x] CI/CD pipeline active
- [ ] 100% core logic test coverage
- [ ] Release binaries / PyPI package

---

## Changelog

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for full version history.
