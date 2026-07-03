# Changelog

## v0.9.11 — 2026-06-17
### Added
- `--config-init` CLI flag generates a starter `config/config.yaml` with the sentinel-based workflow prompt
- Protected by `--force` requirement to overwrite existing configs
- `tests/test_config_init.py` — tests for creation, overwrite refusal, force overwrite, and validation pass
- `RELEASE.md` — release notes summarizing all 32 CLI features, test suite, requirements, and quick start
- `install.sh` updated with `--check` flag for dependency-only validation
- `__version__` bumped to `0.9.11`

## v0.9.10 — 2026-06-17
### Added
- `--config-validate` validates config without starting the loop
- `tests/test_config_validate.py`

## v0.9.9 — 2026-06-17
### Added
- `--webhook-headers <json>` custom HTTP headers for webhooks
- GitHub Actions workflow with Python 3.11/3.12 matrix and coverage upload

## v0.9.8 — 2026-06-17
### Added
- `--webhook <url>` POSTs JSON iteration stats on completion

## v0.9.7 — 2026-06-17
### Added
- `--report <email>`, `--report-file <path>`

## v0.9.6 — 2026-06-17
### Added
- `--benchmark`, `--schedule`

## v0.9.5 — 2026-06-16
### Added
- `--health-check`

## v0.9.12 — Export & Type Hints
### Added
- `--export-stats`, type hints

## v0.9.11 — Sentinel Tests & Clear Stats
### Added
- `--clear-stats`

## v0.9.10 — Statistics & Coverage
### Added
- `--stats`

## v0.9.9 — Log Rotation
### Added
- Auto-rotate at 1MB

## v0.9.8 — Logging to File
### Added
- `--log-file`, `--version`

## v0.9.5 — Verbosity Control
### Added
- `--verbose`, `--quiet`

## v0.9.0 — Focus Control
### Added
- `--no-focus`

## v0.8.5 — Global Runtime Limit
### Added
- `--max-total-time`

## v0.8.0 — Retry Logic
### Added
- `--retry <n>`

## v0.7.5 — Multi-Window Support
### Added
- `--window-index <n>`

## v0.7.0 — Notifications
### Added
- `--sound`, `--sound-file`

## v0.6.0 — Config Profiles
### Added
- `--profile`, `--list-profiles`

## v0.5.0 — Hot Reload
### Added
- Config auto-reload

## v0.4.0 — Live Monitoring
### Added
- `--watch`

## v0.3.0 — Testing Without Windsurf
### Added
- `--simulate`

## v0.2.0 — Pause & Resume
### Added
- Pause sentinel file

## v0.1.0 — Initial Release
### Added
- Sentinel-based loop with `inotifywait`
- xdotool window automation
