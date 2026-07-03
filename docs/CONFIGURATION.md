# Configuration

## File Location

`~/Desktop/cascade-loop/config/config.yaml`

## All Keys

| Key | Type | Default | Description |
|---|---|---|---|
| `iterations` | int | `10` | How many times to run the loop |
| `window_title` | string | `"Windsurf"` | Title of the Windsurf window for `xdotool` to find |
| `sentinel_path` | string | `/tmp/cascade-loop.log` | File the AI writes to when done |
| `pause_file_path` | string | `/tmp/cascade-loop.pause` | If this file exists, the loop pauses between iterations |
| `prompt_template` | string | (see default) | The prompt sent to Cascade. Use `{{ sentinel_path }}`, `{{ iteration }}`, `{{ total }}` |
| `pre_delay` | int | `3` | Seconds to wait after focusing window before typing |
| `post_delay` | int | `5` | Seconds to wait after sentinel before next iteration |
| `timeout` | int | `600` | Max seconds to wait for sentinel per iteration |
| `notifications` | bool | `false` | Enable desktop notifications via `notify-send` |
| `max_total_time` | int | `null` | Global runtime limit in seconds. Loop stops between iterations if exceeded |

## Template Variables

- `{{ sentinel_path }}` — resolves to the configured sentinel file path
- `{{ iteration }}` — current iteration number (1-based)
- `{{ total }}` — total iterations configured

## Example Configs

### Quick Test (3 iterations, fast)
```yaml
iterations: 3
pre_delay: 1
post_delay: 2
timeout: 120
```

### Deep Refactor (slow, safe)
```yaml
iterations: 5
pre_delay: 5
post_delay: 10
timeout: 1800
```

### With Time Limit
```yaml
iterations: 20
max_total_time: 3600
```

### Custom Prompt
```yaml
prompt_template: |
  You are in iteration {{ iteration }} of {{ total }}.
  Implement the next item from .windsurf/plans/roadmap.md.
  Commit your changes with a descriptive message.
  Append "ITERATION_DONE" to {{ sentinel_path }}.
```

## Pause / Resume

Create the pause file to halt the loop between iterations:

```bash
touch /tmp/cascade-loop.pause
```

Remove it to resume:

```bash
rm /tmp/cascade-loop.pause
```

The loop checks for the pause file at the start of each iteration.
