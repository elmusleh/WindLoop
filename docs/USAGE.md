# Usage Guide

## Foreground Mode

Watch the loop run in your terminal:

```bash
cascade-loop --start
```

Press `Ctrl+C` to interrupt.

## Background Mode

Run while you do something else:

```bash
cascade-loop --daemon
cascade-loop --status   # check if running
cascade-loop --stop     # kill it
```

## Config Init

Generate a starter config.yaml:

```bash
cascade-loop --config-init
```

Creates `config/config.yaml` with the sentinel-based workflow prompt and sensible defaults. If config already exists, you must use `--force` to overwrite:

```bash
cascade-loop --config-init --force
```

## Config Validation

Validate your config file without starting the loop:

```bash
cascade-loop --config-validate
```

## Webhook

POST iteration stats to a URL on loop completion:

```bash
cascade-loop --start --webhook https://hooks.slack.com/services/...
```

### Custom Headers

Add custom headers for authentication:

```bash
cascade-loop --start --webhook https://api.example.com/hooks \
  --webhook-headers '{"Authorization": "Bearer token123"}'
```

## Report by Email

Email the HTML iteration report on loop completion:

```bash
cascade-loop --start --report user@example.com
```

## Report to File

Write the HTML report to a custom path:

```bash
cascade-loop --start --report-file ~/reports/cascade-loop.html
```

## Benchmark

Measure per-step timing for a single dry-run iteration:

```bash
cascade-loop --benchmark
```

## Schedule

Delay loop start until a specific wall-clock time:

```bash
cascade-loop --start --schedule 14:00
```

## Health Check

Validate your environment:

```bash
cascade-loop --health-check
```

## Export Statistics

Export iteration data to CSV or HTML:

```bash
cascade-loop --export-stats csv
cascade-loop --export-stats html
```

## Statistics

Print aggregate statistics:

```bash
cascade-loop --stats
```

## Clear Stats

Archive and reset iteration history:

```bash
cascade-loop --clear-stats --force
```

## Redirect Output to File

```bash
cascade-loop --start --log-file /tmp/cascade-loop.log
```

## Skip Window Focusing

```bash
cascade-loop --start --no-focus
```

**Warning:** Without focus, `xdotool` types into whatever window is currently active.

## Global Time Limit

```bash
cascade-loop --start --max-total-time 3600
```

## Retry on Timeout

```bash
cascade-loop --start --retry 3
```

## Custom Config File

```bash
cascade-loop --config /path/to/my-config.yaml
```

## Profile Selection

```bash
cascade-loop --list-profiles
cascade-loop --start --profile quick-test
```

## Multi-Window Support

```bash
cascade-loop --start --window-index 1
```

## Watch Mode (Live Monitor)

```bash
cascade-loop --watch
```

## Simulate Mode

```bash
cascade-loop --simulate
cascade-loop --watch
```

## Sound Alerts

```bash
cascade-loop --start --sound
cascade-loop --start --sound-file /path/to/complete.wav
```

## Desktop Notifications

Enable in `config.yaml`:

```yaml
notifications: true
```

## systemd Service

```bash
systemctl --user start cascade-loop
systemctl --user stop cascade-loop
systemctl --user enable cascade-loop
journalctl --user -u cascade-loop -f
```

## Keyboard Shortcut

**Mint / Cinnamon:** Settings → Keyboard → Shortcuts → Custom → Add
- Name: Cascade Loop Toggle
- Command: `/home/steve/Desktop/cascade-loop/bin/cascade-loop-daemon`
- Binding: `Super+Alt+C`

**GNOME:**
```bash
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Cascade Loop"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "/home/steve/Desktop/cascade-loop/bin/cascade-loop-daemon"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Super><Alt>c"
```

## Dry-Run Test

```bash
cascade-loop --dry-run
cascade-loop --watch
```

## Hot Reload

Edit `config.yaml` mid-loop; changes apply on the next iteration.

## Verbosity Control

```bash
cascade-loop --start --quiet
cascade-loop --start --verbose
```

## Version

```bash
cascade-loop --version
```

## Log Rotation

`logs/iterations.log` auto-rotates at 1MB, keeps 3 backups.

## Test Coverage

```bash
./scripts/coverage.sh
```

## Install

```bash
./install.sh --check   # validate deps only
./install.sh           # full install
```
