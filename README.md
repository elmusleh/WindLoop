# Cascade Loop

Automate AI prompt execution in [Windsurf](https://www.codeium.com/windsurf) Cascade on Linux Mint.

Runs prompts in a loop, detects AI completion via a sentinel file, and provides robust control mechanisms for starting, stopping, and monitoring.

**Version: v0.9.11** | **Test Coverage: ~33%** (46 tests passing)

---

## Features

| Feature | Description |
|---|---|
| **Sentinel Detection** | AI writes `ITERATION_DONE` to a file; the loop waits via `inotifywait` |
| **Pause / Resume** | Sentinel file to halt without killing |
| **Hot Reload** | Edit config mid-loop; changes apply next iteration |
| **Live Monitor** | `--watch` prints real-time iteration table |
| **Retry Logic** | `--retry N` restarts timed-out iterations |
| **Time Limits** | `--max-total-time` caps total runtime |
| **Notifications** | Desktop alerts via `notify-send` |
| **Sound Alerts** | Audio completion tone via `--sound` |
| **Multi-Window** | `--window-index` targets specific Windsurf instance |
| **Config Profiles** | `--profile` loads pre-defined YAML configs |
| **Custom Configs** | `--config` points to arbitrary YAML files |
| **Config Validation** | `--config-validate` checks config without starting |
| **Config Init** | `--config-init` generates starter config |
| **Dry Run** | `--dry-run` tests without submitting |
| **No Focus** | `--no-focus` skips `wmctrl` |
| **Verbosity** | `--verbose` / `--quiet` control log level |
| **Log to File** | `--log-file` redirects output |
| **Log Rotation** | Auto-rotate `iterations.log` at 1MB |
| **Statistics** | `--stats` prints aggregate performance |
| **Export** | `--export-stats csv/html` generates reports |
| **Health Check** | `--health-check` validates dependencies |
| **Benchmark** | `--benchmark` per-step timing |
| **Schedule** | `--schedule HH:MM` delayed start |
| **Email Report** | `--report <email>` emails HTML on completion |
| **Report File** | `--report-file <path>` writes HTML to custom path |
| **Webhook** | `--webhook <url>` POSTs JSON stats on completion |
| **Webhook Headers** | `--webhook-headers <json>` custom auth headers |

---

## Quick Start

```bash
cd ~/Desktop/cascade-loop

# Check dependencies
./install.sh --check

# Install (one-time)
./install.sh

# Generate and validate your config
cascade-loop --config-init
cascade-loop --config-validate

# Run 3 iterations in foreground
cascade-loop --start

# Or run in background
cascade-loop --daemon
cascade-loop --status
cascade-loop --stop

# Monitor progress in another terminal
cascade-loop --watch

# Check your setup
cascade-loop --health-check
```

---

## CLI Flags

```
--start              Run loop in foreground
--daemon             Run in background
--stop               Stop background loop
--status             Show loop status
--dry-run            Test without submitting prompts
--watch              Live monitor
--simulate           Generate fake data for testing
--profile NAME       Load config profile
--list-profiles      List available profiles
--config PATH        Use custom config YAML
--config-validate    Validate config and exit
--config-init        Generate starter config
--window-index N     Target Nth Windsurf window
--sound              Play sound on completion
--sound-file PATH    Use custom audio file
--retry N            Retry timed-out iterations
--max-total-time S   Stop after S seconds total runtime
--no-focus           Skip window focusing
--verbose            Enable debug output
--quiet              Suppress non-essential output
--log-file PATH      Redirect log output to a file
--version            Show version
--stats              Print aggregate statistics
--clear-stats        Archive and reset iteration history
--force              Skip confirmation for --clear-stats / overwrite for --config-init
--export-stats FMT   Export data (csv or html)
--health-check       Check dependencies
--benchmark          Run single dry-run with timing
--schedule HH:MM     Delay start until wall-clock time
--report EMAIL       Email HTML report on completion
--report-file PATH   Write HTML report to custom path
--webhook URL        POST JSON stats to URL on completion
--webhook-headers JSON  Custom headers for webhook
```

---

## Project Structure

```
cascade-loop/
├── src/
│   └── cascade_loop.py
├── config/
│   ├── config.yaml
│   └── profiles/
├── bin/
│   ├── cascade-loop
│   └── cascade-loop-daemon
├── scripts/
│   ├── check.sh
│   ├── test.sh
│   ├── coverage.sh
│   └── install-hooks.sh
├── tests/
│   ├── test_focus.py
│   ├── test_simulate_watch.py
│   ├── test_config_loading.py
│   ├── test_hot_reload.py
│   ├── test_log_levels.py
│   ├── test_daemonize.py
│   ├── test_notifications.py
│   ├── test_sound.py
│   ├── test_stats.py
│   ├── test_sentinel.py
│   ├── test_daemonize_signals.py
│   ├── test_run_loop.py
│   ├── test_health_check.py
│   ├── test_webhook.py
│   ├── test_webhook_headers.py
│   ├── test_report_file.py
│   ├── test_config_validate.py
│   ├── test_config_init.py
│   └── test_test_runner.py
├── .github/
│   └── workflows/
│       └── check.yml
├── systemd/
│   └── cascade-loop.service
├── docs/
│   ├── USAGE.md
│   ├── CONFIGURATION.md
│   ├── ARCHITECTURE.md
│   ├── TROUBLESHOOTING.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   ├── ROADMAP.md
│   └── CHANGELOG.md
├── RELEASE.md
└── install.sh
```

---

## Documentation

- **[Usage Guide](docs/USAGE.md)** — All modes, flags, and examples
- **[Configuration](docs/CONFIGURATION.md)** — All config keys
- **[Architecture](docs/ARCHITECTURE.md)** — Sentinel pattern
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — Common issues
- **[Contributing](docs/CONTRIBUTING.md)** — Dev setup, testing
- **[Security](docs/SECURITY.md)** — Risks
- **[Roadmap](docs/ROADMAP.md)** — Upcoming features
- **[Changelog](docs/CHANGELOG.md)** — Version history
- **[Release Notes](RELEASE.md)** — v0.9.11 release summary

---

## Requirements

- Linux Mint (or any Linux with X11)
- Python 3.11+
- `xdotool`, `wmctrl`, `inotifywait`
- Windsurf with Auto-approve edits enabled

---

## Version

**v0.9.11** — See [CHANGELOG.md](docs/CHANGELOG.md) for full history.
