# Troubleshooting

## Window Not Found

**Symptom:** `[ERROR] Windsurf window not found.`

**Fixes:**
- Is Windsurf running? Start it first.
- Check window title: `xdotool search --name "Windsurf"`
- If title differs (e.g., "Codeium", "Windsurf Editor"), edit `window_title` in `config.yaml`

## Sentinel Timeout

**Symptom:** `TIMEOUT: Sentinel was not written.`

**Causes:**
1. AI failed or errored out without writing sentinel
2. Windsurf auto-approve is OFF; AI is waiting for your click
3. The prompt template does not include the sentinel instruction
4. The AI forgot to write the sentinel (rare)

**Fixes:**
- Enable Auto-approve file edits in Windsurf settings
- Verify `config.yaml` prompt_template ends with sentinel instruction
- Increase `timeout` in `config.yaml`

## Pause / Resume

**Symptom:** The loop seems stuck but there's no timeout error.

**Check:** Did you create a pause file?

```bash
ls -la /tmp/cascade-loop.pause
```

If it exists, remove it:

```bash
rm /tmp/cascade-loop.pause
```

To intentionally pause between iterations:

```bash
touch /tmp/cascade-loop.pause
```

## Focus Not Working

**Symptom:** Windsurf doesn't come to front, or types into wrong window.

**Fixes:**
- Some WMs need `xdotool` with `--sync` flag
- Try `wmctrl -r "Windsurf" -b add,above` instead of `-ia`
- Check if multiple Windsurf windows exist

## Loop Won't Stop

**Symptom:** `cascade-loop --stop` says "Not running" but it's still going.

**Fixes:**
- PID file may be stale: `rm ~/.windsurf/cascade-loop.pid`
- Find process: `ps aux | grep cascade_loop`
- Kill manually: `pkill -f cascade_loop.py`

## systemd Service Fails

**Symptom:** `systemctl --user status cascade-loop` shows failed.

**Fixes:**
- Check that `DISPLAY=:0` is correct (`echo $DISPLAY`)
- Verify `cascade-loop` is in PATH: `which cascade-loop`
- Check logs: `journalctl --user -u cascade-loop`
