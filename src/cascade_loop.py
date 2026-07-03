#!/usr/bin/env python3
from __future__ import annotations
"""Cascade Loop Automation — sends prompts to Windsurf Cascade in a loop."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

__version__ = "0.9.11"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
PROFILES_DIR = PROJECT_ROOT / "config" / "profiles"
PID_PATH = Path.home() / ".windsurf" / "cascade-loop.pid"
LOG_DIR = PROJECT_ROOT / "logs"
JSON_LOG = LOG_DIR / "iterations.json"

DEFAULT_SENTINEL = Path("/tmp") / "cascade-loop.log"
DEFAULT_PAUSE = Path("/tmp") / "cascade-loop.pause"
DONE_MARKER = "ITERATION_DONE"


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"



LOG_LEVEL = 1  # 0=quiet, 1=normal, 2=verbose
LOG_FILE = None
def log(msg: str, level: int = 1, color: str = "") -> None:
    if LOG_LEVEL < level:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    if LOG_FILE:
        try:
            with open(LOG_FILE, "a") as f:
                f.write(line + "\n")
        except OSError as e:
            print(f"[WARN] Cannot write to log file: {e}", file=sys.stderr)
    else:
        print(f"{color}{line}{Colors.RESET}")


def notify(title: str, body: str, urgency: str = "normal") -> None:
    """Send desktop notification if notify-send is available."""
    if subprocess.run(["which", "notify-send"], capture_output=True).returncode != 0:
        return
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, title, body],
            capture_output=True, check=False,
        )
    except FileNotFoundError:
        pass


def play_sound(sound_file: str | None = None) -> None:
    """Play a completion sound. Tries multiple backends in order."""
    if sound_file and Path(sound_file).exists():
        for cmd in [
            ["paplay", sound_file],
            ["aplay", sound_file],
            ["ffplay", "-nodisp", "-autoexit", sound_file],
        ]:
            if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
                subprocess.run(cmd, capture_output=True, check=False)
                return
        log(f"Could not play sound file: {sound_file}", color=Colors.YELLOW)
        return

    # Default system beep
    print("\a", end="", flush=True)
    # Try paplay/aplay on common event sounds
    for cmd in [
        ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
        ["paplay", "/usr/share/sounds/gnome/default/alerts/glass.ogg"],
    ]:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
            if Path(cmd[1]).exists():
                subprocess.run(cmd, capture_output=True, check=False)
                return


def load_config(config_path=None, profile=None):
    path = None
    if config_path:
        path = Path(config_path)
        if not path.exists():
            log(f"Config file not found: {path}", color=Colors.RED)
            sys.exit(1)
        log(f"Loading config: {path}", color=Colors.CYAN)
    elif profile:
        profile_path = PROFILES_DIR / f"{profile}.yaml"
        if profile_path.exists():
            log(f"Loading profile: {profile}", color=Colors.CYAN)
            path = profile_path
        else:
            log(f"Profile not found: {profile_path}", color=Colors.RED)
            log("Falling back to default config.", color=Colors.YELLOW)

    if not path:
        path = DEFAULT_CONFIG_PATH
        if not path.exists():
            log(f"Config not found: {path}", color=Colors.RED)
            sys.exit(1)

    with open(path, "r") as f:
        return yaml.safe_load(f)


def list_profiles():
    """Return available profile names."""
    if not PROFILES_DIR.exists():
        return []
    return sorted([
        p.stem for p in PROFILES_DIR.glob("*.yaml")
    ])


def preflight_checks(config: dict[str, Any]) -> None:
    """Verify system readiness before starting the loop."""
    log("Running pre-flight checks...", level=2, color=Colors.CYAN)

    # Check inotifywait
    if subprocess.run(["which", "inotifywait"], capture_output=True).returncode != 0:
        log("MISSING: inotifywait. Install: sudo apt-get install inotify-tools", color=Colors.RED)
        sys.exit(1)

    # Check xdotool
    if subprocess.run(["which", "xdotool"], capture_output=True).returncode != 0:
        log("MISSING: xdotool. Install: sudo apt-get install xdotool", color=Colors.RED)
        sys.exit(1)

    # Check wmctrl
    if subprocess.run(["which", "wmctrl"], capture_output=True).returncode != 0:
        log("MISSING: wmctrl. Install: sudo apt-get install wmctrl", color=Colors.RED)
        sys.exit(1)

    # Check Windsurf window
    title = config.get("window_title", "Windsurf")
    result = subprocess.run(
        ["xdotool", "search", "--name", title],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        log(f"Windsurf window not found (title: '{title}'). Is it running?", color=Colors.RED)
        log(f"Tip: Change 'window_title' in config.yaml if the title differs.", color=Colors.YELLOW)
        sys.exit(1)
    log(f"Found Windsurf window (title: '{title}')", color=Colors.GREEN)

    # Warn about auto-approve
    log("=" * 50, color=Colors.YELLOW)
    log("IMPORTANT: Ensure Windsurf Auto-approve edits is ON", color=Colors.YELLOW + Colors.BOLD)
    log("Settings -> Cascade -> Auto-approve file edits", color=Colors.YELLOW)
    log("Without this, the loop will hang waiting for your click.", Colors.YELLOW)
    log("=" * 50, color=Colors.YELLOW)
    time.sleep(2)


def find_windsurf_window(title: str = "Windsurf", index: int = 0) -> str:
    log(f"Searching for window: {title} (index={index})", level=2, color=Colors.CYAN)
    result = subprocess.run(
        ["xdotool", "search", "--name", title],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        log(f"Windsurf window not found (title: '{title}').", color=Colors.RED)
        sys.exit(1)

    windows = result.stdout.strip().split("\n")
    if len(windows) > 1 and index == 0:
        log(f"WARNING: Multiple Windsurf windows found ({len(windows)}).", color=Colors.YELLOW)
        log(f"Using window index 0. Use --window-index to select another.", color=Colors.YELLOW)

    if index >= len(windows):
        log(f"Window index {index} out of range (found {len(windows)} windows).", color=Colors.RED)
        sys.exit(1)

    return windows[index]


def focus_window(window_id: str) -> None:
    log(f"Focusing window {window_id}", level=2, color=Colors.CYAN)
    subprocess.run(["wmctrl", "-ia", window_id], check=False)
    time.sleep(0.5)


def open_cascade_chat():
    subprocess.run(["xdotool", "key", "ctrl+shift+p"], check=False)
    time.sleep(0.5)
    subprocess.run(["xdotool", "type", "Open Cascade Chat"], check=False)
    time.sleep(0.3)
    subprocess.run(["xdotool", "key", "Return"], check=False)
    time.sleep(0.5)


def focus_chat_input():
    subprocess.run(["xdotool", "key", "Tab"], check=False)
    time.sleep(0.2)


def type_prompt(text):
    subprocess.run(["xdotool", "type", "--delay", "10", text], check=False)
    time.sleep(0.2)


def submit_prompt():
    subprocess.run(["xdotool", "key", "Return"], check=False)


def check_pause(pause_path):
    """If pause file exists, block until it is removed."""
    pause_path = Path(pause_path)
    if not pause_path.exists():
        return
    log(f"PAUSE detected: {pause_path}", color=Colors.CYAN + Colors.BOLD)
    notify("Cascade Loop Paused", "Remove the pause file to resume.", urgency="normal")
    log("Remove the file to resume.", color=Colors.CYAN)
    while pause_path.exists():
        time.sleep(5)
    log("RESUMED — pause file removed.", color=Colors.GREEN)
    notify("Cascade Loop Resumed", "Continuing iterations.", urgency="low")


def wait_for_sentinel(sentinel_path, timeout_sec=600):
    sentinel_path = Path(sentinel_path)
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)

    if not sentinel_path.exists():
        sentinel_path.write_text("")

    log(f"Waiting for sentinel: {sentinel_path} (timeout {timeout_sec}s)", color=Colors.CYAN)
    try:
        proc = subprocess.Popen(
            ["inotifywait", "-q", "-e", "modify,close_write", str(sentinel_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            proc.wait(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            log("TIMEOUT: Sentinel was not written. Possible causes:", color=Colors.RED + Colors.BOLD)
            log("  1. AI failed or errored out", color=Colors.YELLOW)
            log("  2. Auto-approve edits is OFF — AI is waiting for your click", color=Colors.YELLOW)
            log("  3. The prompt template is missing the sentinel instruction", color=Colors.YELLOW)
            log("  4. The AI forgot to write the sentinel (rare)", color=Colors.YELLOW)
            return False
    except FileNotFoundError:
        log("inotifywait not found. Install: sudo apt-get install inotify-tools", color=Colors.RED)
        sys.exit(1)

    content = sentinel_path.read_text()
    if DONE_MARKER in content:
        return True
    log("Sentinel file changed but marker not found yet. Retrying...", color=Colors.YELLOW)
    return wait_for_sentinel(sentinel_path, timeout_sec=60)


def append_iteration_log(iteration, status, duration=0, error=""):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "iterations.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} | Iteration {iteration} | {status} | {duration:.1f}s | {error}\n")


def write_json_log(iteration, status, duration, error="", files_modified=None, start_time=None, retries=0):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "iteration": iteration,
        "status": status,
        "start_time": (start_time or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        "end_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_sec": round(duration, 2),
        "error": error,
        "files_modified": files_modified or [],
        "retries": retries,
    }

    records = []
    if JSON_LOG.exists():
        try:
            with open(JSON_LOG, "r") as f:
                records = json.load(f)
        except json.JSONDecodeError:
            records = []

    records.append(entry)

    tmp = JSON_LOG.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(records, f, indent=2)
    tmp.replace(JSON_LOG)


def run_loop(config, config_path=None, dry_run=False, window_index=0, sound_file=None, retry=0, max_total_time=None, no_focus=False):
    window_title = config.get("window_title", "Windsurf")
    sentinel_path = config.get("sentinel_path", str(DEFAULT_SENTINEL))
    pause_path = config.get("pause_file_path", str(DEFAULT_PAUSE))
    prompt_template = config.get("prompt_template", "")
    pre_delay = config.get("pre_delay", 2)
    post_delay = config.get("post_delay", 3)
    timeout = config.get("timeout", 600)
    notifications = config.get("notifications", False)
    iterations = config.get("iterations", 1)
    enable_sound = config.get("sound", False) or sound_file is not None
    max_total_time = max_total_time or config.get("max_total_time", None)

    window_id = find_windsurf_window(window_title, index=window_index)

    # Track config hash for hot reload
    last_config_str = json.dumps(config, sort_keys=True)

    total_elapsed = 0.0
    loop_start_time = time.time()

    for i in range(1, iterations + 1):
        # Check global time limit before starting iteration
        if max_total_time is not None:
            total_elapsed = time.time() - loop_start_time
            if total_elapsed >= max_total_time:
                log(f"Global time limit reached ({max_total_time}s) — stopping.", color=Colors.YELLOW + Colors.BOLD)
                if notifications:
                    notify("Cascade Loop Stopped", f"Time limit {max_total_time}s reached after {total_elapsed:.0f}s.", urgency="normal")
                break

        # Hot reload: re-read config at start of each iteration
        if config_path and i > 1:
            try:
                with open(config_path, "r") as f:
                    fresh = yaml.safe_load(f)
                fresh_str = json.dumps(fresh, sort_keys=True)
                if fresh_str != last_config_str:
                    log("Config changed — reloading.", level=2, color=Colors.CYAN + Colors.BOLD)
                    config = fresh
                    last_config_str = fresh_str
                    # Update local vars from reloaded config
                    window_title = config.get("window_title", window_title)
                    sentinel_path = config.get("sentinel_path", sentinel_path)
                    pause_path = config.get("pause_file_path", pause_path)
                    prompt_template = config.get("prompt_template", prompt_template)
                    pre_delay = config.get("pre_delay", pre_delay)
                    post_delay = config.get("post_delay", post_delay)
                    timeout = config.get("timeout", timeout)
                    notifications = config.get("notifications", notifications)
                    enable_sound = config.get("sound", False) or sound_file is not None
                    max_total_time = max_total_time or config.get("max_total_time", None)
            except Exception as e:
                log(f"Config reload failed: {e}", color=Colors.YELLOW)

        check_pause(pause_path)

        log(f"{'='*40}", color=Colors.BOLD)
        log(f"Starting iteration {i}/{iterations}", color=Colors.BOLD)
        log(f"{'='*40}", color=Colors.BOLD)

        t_start = time.time()
        dt_start = datetime.now()
        if not no_focus:
            focus_window(window_id)
        time.sleep(pre_delay)

        open_cascade_chat()
        focus_chat_input()

        prompt = prompt_template.replace("{{ sentinel_path }}", str(sentinel_path))
        prompt = prompt.replace("{{ iteration }}", str(i))
        prompt = prompt.replace("{{ total }}", str(iterations))

        type_prompt(prompt)

        if dry_run:
            log("DRY-RUN: Would submit prompt now. Skipping.", color=Colors.CYAN)
            duration = time.time() - t_start
            append_iteration_log(i, "dry-run", duration)
            write_json_log(i, "dry-run", duration, start_time=dt_start.strftime("%Y-%m-%dT%H:%M:%S"))
            time.sleep(2)
            continue

        submit_prompt()
        log("Prompt submitted. Waiting for AI to finish...", color=Colors.CYAN)

        retry_count = 0
        success = False
        while True:
            success = wait_for_sentinel(sentinel_path, timeout)
            if success:
                break
            retry_count += 1
            if retry_count <= retry:
                log(f"Retrying iteration {i} (attempt {retry_count + 1}/{retry + 1})", color=Colors.YELLOW + Colors.BOLD)
                if notifications:
                    notify("Cascade Loop Retry", f"Iteration {i} retry {retry_count}/{retry}", urgency="normal")
            else:
                break

        duration = time.time() - t_start

        if success:
            log(f"Iteration {i} complete in {duration:.1f}s", color=Colors.GREEN)
            append_iteration_log(i, "done", duration)
            write_json_log(i, "done", duration, start_time=dt_start.strftime("%Y-%m-%dT%H:%M:%S"), retries=retry_count)
            if notifications:
                notify("Cascade Loop", f"Iteration {i}/{iterations} complete ({duration:.0f}s)", urgency="low")
        else:
            log(f"Iteration {i} FAILED after {duration:.1f}s ({retry_count} retries exhausted)", color=Colors.RED + Colors.BOLD)
            append_iteration_log(i, "timeout", duration, "sentinel_timeout")
            write_json_log(i, "timeout", duration, "sentinel_timeout", start_time=dt_start.strftime("%Y-%m-%dT%H:%M:%S"), retries=retry_count)
            if notifications:
                notify("Cascade Loop FAILED", f"Iteration {i} timed out after {duration:.0f}s ({retry_count} retries)", urgency="critical")
            log("Stopping loop.", color=Colors.RED)
            break

        time.sleep(post_delay)

    log("Loop finished.", color=Colors.GREEN + Colors.BOLD)
    if notifications:
        notify("Cascade Loop Complete", f"Finished {i}/{iterations} iterations.", urgency="normal")
    if enable_sound:
        play_sound(sound_file)


def watch_mode():
    """Tail iterations.json and print a live status table."""
    log("Starting watch mode. Press Ctrl+C to exit.", color=Colors.CYAN + Colors.BOLD)
    log(f"Monitoring: {JSON_LOG}", color=Colors.CYAN)

    def print_table(records):
        os.system("clear" if os.name != "nt" else "cls")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  Cascade Loop — Live Monitor{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{'Iter':>5} {'Status':>10} {'Duration':>10} {'Error':>15}")
        print("-" * 60)
        for r in records:
            color = Colors.GREEN if r.get("status") == "done" else Colors.RED if r.get("status") == "timeout" else Colors.YELLOW
            print(f"{r.get('iteration', 0):>5} {color}{r.get('status', '?'):>10}{Colors.RESET} {r.get('duration_sec', 0):>9.1f}s {r.get('error', ''):>15}")
        print("-" * 60)
        total = len(records)
        done = sum(1 for r in records if r.get("status") == "done")
        print(f"Total: {total} | Done: {done} | Pending: {total - done}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print("\nWaiting for updates... (Ctrl+C to quit)")

    last_mtime = 0
    try:
        while True:
            mtime = JSON_LOG.stat().st_mtime if JSON_LOG.exists() else 0
            if mtime != last_mtime:
                last_mtime = mtime
                records = []
                if JSON_LOG.exists():
                    try:
                        with open(JSON_LOG, "r") as f:
                            records = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        pass
                print_table(records)
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Watch mode exited.{Colors.RESET}")
        sys.exit(0)


def simulate_mode():
    """Generate fake iteration data for testing --watch without Windsurf."""
    log("SIMULATE mode — generating fake iteration data.", color=Colors.CYAN + Colors.BOLD)
    log(f"WARNING: This will overwrite {JSON_LOG}", color=Colors.YELLOW)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    fake_data = [
        {
            "iteration": 1,
            "status": "done",
            "start_time": (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": (now - timedelta(minutes=4, seconds=15)).strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_sec": 45.3,
            "error": "",
            "files_modified": ["src/app.py", "tests/test_app.py"],
        },
        {
            "iteration": 2,
            "status": "done",
            "start_time": (now - timedelta(minutes=3, seconds=50)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": (now - timedelta(minutes=2, seconds=20)).strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_sec": 90.0,
            "error": "",
            "files_modified": ["src/utils.py"],
        },
        {
            "iteration": 3,
            "status": "timeout",
            "start_time": (now - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": (now).strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_sec": 600.0,
            "error": "sentinel_timeout",
            "files_modified": [],
        },
        {
            "iteration": 4,
            "status": "dry-run",
            "start_time": (now - timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": (now - timedelta(seconds=28)).strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_sec": 2.0,
            "error": "",
            "files_modified": [],
        },
        {
            "iteration": 5,
            "status": "done",
            "start_time": (now - timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": (now - timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_sec": 15.0,
            "error": "",
            "files_modified": ["README.md", "docs/USAGE.md"],
        },
    ]

    tmp = JSON_LOG.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(fake_data, f, indent=2)
    tmp.replace(JSON_LOG)

    log(f"Wrote {len(fake_data)} fake iterations to {JSON_LOG}", color=Colors.GREEN)
    log("Now run: cascade-loop --watch", color=Colors.CYAN + Colors.BOLD)




def stats_mode():
    """Print aggregate statistics from iterations.json."""
    if not JSON_LOG.exists():
        log("No iteration data found. Run the loop or use --simulate first.", color=Colors.YELLOW)
        sys.exit(0)

    try:
        with open(JSON_LOG, "r") as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"Cannot read iterations.json: {e}", color=Colors.RED)
        sys.exit(1)

    if not records:
        log("No iteration data yet.", color=Colors.YELLOW)
        sys.exit(0)

    total = len(records)
    done = sum(1 for r in records if r.get("status") == "done")
    timeouts = sum(1 for r in records if r.get("status") == "timeout")
    dry_runs = sum(1 for r in records if r.get("status") == "dry-run")
    retries = sum(r.get("retries", 0) for r in records)
    durations = [r.get("duration_sec", 0) for r in records]
    avg_duration = sum(durations) / len(durations) if durations else 0
    success_rate = (done / total * 100) if total else 0
    latest = records[-1].get("end_time", "N/A")

    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  Cascade Loop Statistics{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"  Total iterations:    {total}")
    print(f"  Successful:          {done} ({success_rate:.1f}%)")
    print(f"  Timeouts:            {timeouts}")
    print(f"  Dry-runs:            {dry_runs}")
    print(f"  Total retries:       {retries}")
    print(f"  Avg duration:        {avg_duration:.1f}s")
    print(f"  Latest entry:        {latest}")
    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")



def clear_stats_mode(force=False):
    """Archive and reset iteration history files."""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived = []

    for src_name in ["iterations.json", "iterations.log"]:
        src = LOG_DIR / src_name
        if src.exists():
            dst = LOG_DIR / f"{src_name}.{timestamp}"
            shutil.copy2(str(src), str(dst))
            archived.append(str(dst))

    if not archived:
        log("No stats to clear.", color=Colors.YELLOW)
        sys.exit(0)

    if not force:
        log(f"Archive {len(archived)} file(s)? Press y + Enter to confirm.", color=Colors.CYAN)
        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm != "y":
            log("Aborted. Nothing was cleared.", color=Colors.YELLOW)
            sys.exit(0)

    for src_name in ["iterations.json", "iterations.log"]:
        src = LOG_DIR / src_name
        if src.exists():
            src.unlink()

    log(f"Cleared. Archived to:", color=Colors.GREEN)
    for a in archived:
        log(f"  {a}", color=Colors.GREEN)



def export_stats_mode(fmt: str = "csv") -> None:
    """Export iteration data to CSV or HTML format."""
    if not JSON_LOG.exists():
        log("No iteration data to export.", color=Colors.YELLOW)
        sys.exit(0)

    try:
        with open(JSON_LOG, "r") as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"Cannot read iterations.json: {e}", color=Colors.RED)
        sys.exit(1)

    if not records:
        log("No iteration data to export.", color=Colors.YELLOW)
        sys.exit(0)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        import csv
        output = LOG_DIR / "iterations.csv"
        if records:
            fieldnames = list(records[0].keys())
            with open(output, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
        log(f"Exported {len(records)} records to {output}", color=Colors.GREEN)
    elif fmt == "html":
        output = LOG_DIR / "iterations.html"
        rows = []
        headers = list(records[0].keys()) if records else []
        for r in records:
            cells = "".join(f"<td>{r.get(h, '')}</td>" for h in headers)
            rows.append(f"<tr>{cells}</tr>")
        header_row = "".join(f"<th>{h}</th>" for h in headers)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Iteration Report</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left}}
th{{background:#f4f4f4}}tr:nth-child(even){{background:#fafafa}}</style>
</head><body><h1>Iteration Report</h1>
<table><thead><tr>{header_row}</tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Total: {len(records)} iterations</p></body></html>"""
        with open(output, "w") as f:
            f.write(html)
        log(f"Exported {len(records)} records to {output}", color=Colors.GREEN)



def health_check_mode() -> None:
    """Validate dependencies and print a colored status table."""
    checks = [
        ("xdotool", "Window automation"),
        ("wmctrl", "Window focus control"),
        ("inotifywait", "Sentinel file monitoring"),
        ("notify-send", "Desktop notifications (optional)"),
    ]

    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  Cascade Loop Health Check{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")

    critical_ok = 0
    critical_total = 3  # xdotool, wmctrl, inotifywait

    for cmd, desc in checks:
        result = subprocess.run(["which", cmd], capture_output=True)
        if result.returncode == 0:
            status = f"{Colors.GREEN}OK{Colors.RESET}"
            if "optional" not in desc:
                critical_ok += 1
        else:
            status = f"{Colors.RED}MISSING{Colors.RESET}"
        print(f"  {cmd:18s} {desc:30s} {status}")

    # Check audio player
    audio_found = False
    for player in ["paplay", "aplay", "ffplay"]:
        if subprocess.run(["which", player], capture_output=True).returncode == 0:
            audio_found = True
            print(f"  {player:18s} Audio playback (optional)       {Colors.GREEN}OK{Colors.RESET}")
            break
    if not audio_found:
        print(f"  {'audio player':18s} Audio playback (optional)       {Colors.YELLOW}NOT FOUND{Colors.RESET}")

    # Check Windsurf window
    result = subprocess.run(["xdotool", "search", "--name", "Windsurf"], capture_output=True)
    if result.returncode == 0:
        print(f"  {'Windsurf window':18s} Window detection                {Colors.GREEN}FOUND{Colors.RESET}")
    else:
        print(f"  {'Windsurf window':18s} Window detection                {Colors.YELLOW}NOT RUNNING{Colors.RESET}")

    # Check config
    if DEFAULT_CONFIG_PATH.exists():
        try:
            with open(DEFAULT_CONFIG_PATH, "r") as f:
                yaml.safe_load(f)
            print(f"  {'config.yaml':18s} Config file                     {Colors.GREEN}OK{Colors.RESET}")
        except Exception:
            print(f"  {'config.yaml':18s} Config file                     {Colors.RED}INVALID{Colors.RESET}")
    else:
        print(f"  {'config.yaml':18s} Config file                     {Colors.RED}MISSING{Colors.RESET}")

    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"  Critical deps: {critical_ok}/{critical_total}")

    if critical_ok == critical_total:
        print(f"  {Colors.GREEN}All critical dependencies satisfied.{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"  {Colors.RED}Some critical dependencies are missing. Install with:")
        print(f"    sudo apt-get install xdotool wmctrl inotify-tools")
        print(f"  {Colors.RESET}")
        sys.exit(1)



def benchmark_mode(config: dict[str, Any]) -> None:
    """Run a single dry-run iteration with per-step timing."""
    log("Starting benchmark mode (1 dry-run iteration)...", color=Colors.CYAN + Colors.BOLD)
    import time as time_module

    times: dict[str, float] = {}
    t0 = time_module.perf_counter()

    window_id = find_windsurf_window(config.get("window_title", "Windsurf"))
    times["find_window"] = time_module.perf_counter() - t0

    t1 = time_module.perf_counter()
    focus_window(window_id)
    times["focus_window"] = time_module.perf_counter() - t1

    t1 = time_module.perf_counter()
    open_cascade_chat()
    times["open_chat"] = time_module.perf_counter() - t1

    t1 = time_module.perf_counter()
    focus_chat_input()
    times["focus_input"] = time_module.perf_counter() - t1

    prompt = config.get("prompt_template", "").replace("{{ iteration }}", str(1)).replace("{{ total }}", str(1))
    t1 = time_module.perf_counter()
    type_prompt(prompt)
    times["type_prompt"] = time_module.perf_counter() - t1

    t1 = time_module.perf_counter()
    time_module.sleep(config.get("post_delay", 0))
    times["post_delay"] = time_module.perf_counter() - t1

    total = time_module.perf_counter() - t0

    print("\n" + Colors.BOLD + "="*50 + Colors.RESET)
    print(Colors.CYAN + Colors.BOLD + "  Benchmark Results" + Colors.RESET)
    print(Colors.BOLD + "="*50 + Colors.RESET)
    for step, dt in times.items():
        print(f"  {step:18s} {dt*1000:8.1f} ms")
    print("  " + "-"*40)
    print(f"  {'total':18s} " + Colors.GREEN + f"{total*1000:8.1f} ms" + Colors.RESET)
    print(Colors.BOLD + "="*50 + Colors.RESET)


def schedule_sleep(schedule_str: str) -> None:
    """Sleep until the specified HH:MM time."""
    from datetime import datetime, timedelta
    now = datetime.now()
    try:
        hour, minute = map(int, schedule_str.split(":"))
    except ValueError:
        log(f"Invalid schedule format: {schedule_str}. Use HH:MM (24h).", color=Colors.RED)
        sys.exit(1)

    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)

    wait_seconds = (target - now).total_seconds()
    log(f"Scheduled to start at {target.strftime('%Y-%m-%d %H:%M')}", color=Colors.CYAN)
    log(f"Waiting {wait_seconds:.0f} seconds...", color=Colors.CYAN)

    if LOG_LEVEL >= 2:
        # Verbose: print countdown every 60s
        while wait_seconds > 60:
            time.sleep(60)
            wait_seconds -= 60
            log(f"  {wait_seconds:.0f}s remaining...", level=2)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
    else:
        time.sleep(wait_seconds)

    log("Scheduled start time reached. Starting loop.", color=Colors.GREEN)



def send_report(email: str, html_content: str) -> None:
    """Send HTML report via sendmail or msmtp."""
    import email.mime.text
    import email.mime.multipart
    import shutil

    msg = email.mime.multipart.MIMEMultipart("alternative")
    msg["Subject"] = "Cascade Loop Iteration Report"
    msg["From"] = "cascade-loop@localhost"
    msg["To"] = email
    msg.attach(email.mime.text.MIMEText(html_content, "html"))

    body = msg.as_bytes()
    mailer = None
    for candidate in ["sendmail", "msmtp"]:
        if shutil.which(candidate):
            mailer = candidate
            break

    if not mailer:
        log("No mailer (sendmail/msmtp) found. Skipping email report.", color=Colors.YELLOW)
        return

    try:
        if mailer == "sendmail":
            proc = subprocess.run(
                ["sendmail", "-t"],
                input=body,
                capture_output=True,
            )
        else:
            proc = subprocess.run(
                ["msmtp", "-t", email],
                input=body,
                capture_output=True,
            )
        if proc.returncode == 0:
            log(f"Report emailed to {email}", color=Colors.GREEN)
        else:
            log(f"Email failed (exit {proc.returncode}): {proc.stderr.decode()[:200]}", color=Colors.RED)
    except Exception as e:
        log(f"Email error: {e}", color=Colors.RED)


def write_report_file(path: str) -> None:
    """Write HTML report to a custom file path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not JSON_LOG.exists():
        log("No iteration data to report.", color=Colors.YELLOW)
        return
    try:
        with open(JSON_LOG, "r") as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"Cannot read iterations.json: {e}", color=Colors.RED)
        return
    if not records:
        log("No iteration data to report.", color=Colors.YELLOW)
        return

    headers = list(records[0].keys()) if records else []
    rows = []
    for r in records:
        cells = "".join(f"<td>{r.get(h, '')}</td>" for h in headers)
        rows.append(f"<tr>{cells}</tr>")
    header_row = "".join(f"<th>{h}</th>" for h in headers)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Iteration Report</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left}}
th{{background:#f4f4f4}}tr:nth-child(even){{background:#fafafa}}</style>
</head><body><h1>Iteration Report</h1>
<table><thead><tr>{header_row}</tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Total: {len(records)} iterations</p></body></html>"""

    try:
        with open(target, "w") as f:
            f.write(html)
        log(f"Report written to {target}", color=Colors.GREEN)
    except OSError as e:
        log(f"Cannot write report file: {e}", color=Colors.RED)



def send_webhook(url: str, headers_json: str | None = None) -> None:
    """POST iteration stats to a webhook URL on loop completion."""
    import urllib.request
    import urllib.error

    if not JSON_LOG.exists():
        log("No iteration data for webhook.", color=Colors.YELLOW)
        return

    try:
        with open(JSON_LOG, "r") as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"Cannot read iterations.json for webhook: {e}", color=Colors.RED)
        return

    total = len(records)
    done = sum(1 for r in records if r.get("status") == "done")
    timeouts = sum(1 for r in records if r.get("status") == "timeout")
    dry_runs = sum(1 for r in records if r.get("status") == "dry-run")
    durations = [r.get("duration_sec", 0) for r in records]
    avg_duration = sum(durations) / len(durations) if durations else 0
    success_rate = (done / total * 100) if total else 0

    payload = {
        "source": "cascade-loop",
        "version": __version__,
        "total_iterations": total,
        "successful": done,
        "success_rate": round(success_rate, 1),
        "timeouts": timeouts,
        "dry_runs": dry_runs,
        "avg_duration_sec": round(avg_duration, 1),
        "timestamp": datetime.now().isoformat(),
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if headers_json:
        try:
            custom = json.loads(headers_json)
            if isinstance(custom, dict):
                headers.update({k: str(v) for k, v in custom.items()})
            else:
                log("Webhook headers must be a JSON object. Ignoring.", color=Colors.YELLOW)
        except json.JSONDecodeError as e:
            log(f"Invalid webhook headers JSON: {e}. Ignoring.", color=Colors.YELLOW)

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log(f"Webhook POST {url} -> {resp.status}", color=Colors.GREEN)
    except urllib.error.HTTPError as e:
        log(f"Webhook HTTP error: {e.code} {e.reason}", color=Colors.RED)
    except urllib.error.URLError as e:
        log(f"Webhook URL error: {e.reason}", color=Colors.RED)
    except Exception as e:
        log(f"Webhook failed: {e}", color=Colors.RED)



def validate_config_mode(config_path: str | None = None) -> None:
    """Parse config file and report all errors without starting the loop."""
    path = Path(config_path) if config_path else CONFIG_PATH

    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  Config Validation{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"  File: {path}")

    # Check file exists and is readable
    if not path.exists():
        print(f"  {Colors.RED}FAIL{Colors.RESET}  File not found")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(1)

    if not os.access(path, os.R_OK):
        print(f"  {Colors.RED}FAIL{Colors.RESET}  File not readable")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(1)

    # Check YAML parses
    try:
        with open(path, "r") as f:
            raw = f.read()
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        print(f"  {Colors.RED}FAIL{Colors.RESET}  Invalid YAML: {e}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(1)
    except OSError as e:
        print(f"  {Colors.RED}FAIL{Colors.RESET}  Cannot read file: {e}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(1)

    if data is None:
        print(f"  {Colors.YELLOW}WARN{Colors.RESET}  File is empty")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(1)

    print(f"  {Colors.GREEN}OK{Colors.RESET}   YAML parseable")

    # Required keys
    required = {
        "prompt_template": str,
    }
    optional = {
        "window_title": str,
        "post_delay": (int, float),
        "max_total_time": (int, float),
        "retry": int,
        "notifications": bool,
        "log_file": str,
        "sound_file": str,
        "profile": str,
    }

    errors = 0
    for key, expected_type in required.items():
        if key not in data:
            print(f"  {Colors.RED}FAIL{Colors.RESET}  Missing required key: '{key}'")
            errors += 1
        elif not isinstance(data[key], expected_type):
            print(f"  {Colors.RED}FAIL{Colors.RESET}  Key '{key}' has wrong type: expected {expected_type.__name__}, got {type(data[key]).__name__}")
            errors += 1
        else:
            print(f"  {Colors.GREEN}OK{Colors.RESET}   Required key '{key}'")

    for key, expected_type in optional.items():
        if key in data:
            if not isinstance(data[key], expected_type):
                print(f"  {Colors.YELLOW}WARN{Colors.RESET}  Optional key '{key}' has wrong type: expected {expected_type.__name__ if isinstance(expected_type, type) else ' or '.join(t.__name__ for t in expected_type)}, got {type(data[key]).__name__}")
                errors += 1
            else:
                print(f"  {Colors.GREEN}OK{Colors.RESET}   Optional key '{key}'")

    # Validate prompt_template placeholders (informational only)
    if "prompt_template" in data and isinstance(data["prompt_template"], str):
        tmpl = data["prompt_template"]
        if "{{ iteration }}" not in tmpl and "{{iteration}}" not in tmpl:
            print(f"  {Colors.YELLOW}INFO{Colors.RESET}  prompt_template missing '{{{{ iteration }}}}' placeholder (optional)")
        else:
            print(f"  {Colors.GREEN}OK{Colors.RESET}   prompt_template has iteration placeholder")

    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    if errors == 0:
        print(f"  {Colors.GREEN}{Colors.BOLD}All checks passed. Config is valid.{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"  {Colors.RED}{Colors.BOLD}{errors} error(s) found.{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        sys.exit(1)



def init_config_mode(force: bool = False) -> None:
    """Generate a starter config.yaml with sensible defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if DEFAULT_CONFIG_PATH.exists() and not force:
        log(f"Config already exists at {DEFAULT_CONFIG_PATH}. Use --force to overwrite.", color=Colors.YELLOW)
        sys.exit(1)

    default_config = """# Cascade Loop Configuration
# See docs/CONFIGURATION.md for all options

prompt_template: |
  Read the active plan in .windsurf/plans/active-plan.md.
  Implement the next pending Recommended Next Step.
  Update the tracker with what was done.
  As your VERY LAST action, append the line "ITERATION_DONE" to {{ sentinel_path }}.

window_title: "Windsurf"
pre_delay: 3
post_delay: 5
timeout: 600

# Optional settings (uncomment to enable):
# max_total_time: 3600
# retry: 3
# notifications: true
# sound_file: assets/complete.wav
"""

    try:
        with open(DEFAULT_CONFIG_PATH, "w") as f:
            f.write(default_config)
        log(f"Starter config written to {DEFAULT_CONFIG_PATH}", color=Colors.GREEN)
    except OSError as e:
        log(f"Cannot write config: {e}", color=Colors.RED)
        sys.exit(1)

def write_pid():
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_PATH, "w") as f:
        f.write(str(os.getpid()))


def read_pid():
    if not PID_PATH.exists():
        return None
    try:
        return int(PID_PATH.read_text().strip())
    except ValueError:
        return None


def remove_pid():
    if PID_PATH.exists():
        PID_PATH.unlink()


def is_running(pid):
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def daemonize(config, config_path=None, window_index=0, sound_file=None, retry=0, max_total_time=None, no_focus=False):
    pid = read_pid()
    if pid and is_running(pid):
        log(f"Already running (PID {pid}).", color=Colors.YELLOW)
        sys.exit(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        log(f"Fork failed: {e}", color=Colors.RED)
        sys.exit(1)

    os.chdir(str(PROJECT_ROOT))
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        log(f"Fork 2 failed: {e}", color=Colors.RED)
        sys.exit(1)

    write_pid()

    def cleanup(signum, frame):
        log("Caught signal — shutting down.", color=Colors.YELLOW)
        remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    run_loop(config, config_path=config_path, window_index=window_index, sound_file=sound_file, retry=retry, max_total_time=max_total_time, no_focus=no_focus)
    remove_pid()


def main():
    parser = argparse.ArgumentParser(description="Cascade Loop Automation")
    parser.add_argument("--start", action="store_true", help="Run loop in foreground (default)")
    parser.add_argument("--daemon", action="store_true", help="Run in background")
    parser.add_argument("--stop", action="store_true", help="Stop background loop")
    parser.add_argument("--status", action="store_true", help="Show loop status")
    parser.add_argument("--dry-run", action="store_true", help="Test without submitting")
    parser.add_argument("--watch", action="store_true", help="Watch iterations.json live")
    parser.add_argument("--simulate", action="store_true", help="Generate fake data for testing --watch")
    parser.add_argument("--profile", type=str, default=None, help="Load config profile (e.g., quick-test, deep-refactor)")
    parser.add_argument("--list-profiles", action="store_true", help="List available config profiles")
    parser.add_argument("--config", type=str, default=None, help="Path to custom config YAML file")
    parser.add_argument("--window-index", type=int, default=0, help="Index of Windsurf window if multiple exist (0-based)")
    parser.add_argument("--sound", action="store_true", help="Play sound on loop completion")
    parser.add_argument("--sound-file", type=str, default=None, help="Path to custom audio file (.wav/.ogg)")
    parser.add_argument("--retry", type=int, default=0, help="Retry timed-out iterations up to N times")
    parser.add_argument("--max-total-time", type=int, default=None, help="Stop loop after total runtime exceeds N seconds")
    parser.add_argument("--no-focus", action="store_true", help="Skip window focusing (Windsurf must already be active)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output (only errors/warnings)")
    parser.add_argument("--log-file", type=str, default=None, help="Redirect log output to a file")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--stats", action="store_true", help="Print aggregate statistics from iterations.json")
    parser.add_argument("--clear-stats", action="store_true", help="Archive and reset iteration history")
    parser.add_argument("--force", action="store_true", help="Skip confirmation for --clear-stats")
    parser.add_argument("--export-stats", type=str, choices=["csv", "html"], default=None, help="Export iteration data (csv or html)")
    parser.add_argument("--health-check", action="store_true", help="Check dependencies and print status table")
    parser.add_argument("--benchmark", action="store_true", help="Run a single dry-run iteration with per-step timing")
    parser.add_argument("--schedule", type=str, default=None, help="Delay start until HH:MM (24h)")
    parser.add_argument("--report", type=str, default=None, help="Email HTML report to address on completion")
    parser.add_argument("--report-file", type=str, default=None, dest="report_file", help="Write HTML report to custom path on completion")
    parser.add_argument("--webhook", type=str, default=None, help="POST JSON stats to URL on completion")
    parser.add_argument("--webhook-headers", type=str, default=None, dest="webhook_headers", help="Custom JSON headers for webhook")
    parser.add_argument("--config-validate", action="store_true", dest="config_validate", help="Validate config and exit without starting loop")
    parser.add_argument("--config-init", action="store_true", dest="config_init", help="Generate a starter config.yaml")
    args = parser.parse_args()

    if args.version:
        print(f"cascade-loop {__version__}")
        sys.exit(0)

    if args.stats:
        stats_mode()
        sys.exit(0)

    if args.clear_stats:
        clear_stats_mode(force=args.force)
        sys.exit(0)

    if args.export_stats:
        export_stats_mode(fmt=args.export_stats)
        sys.exit(0)

    if args.health_check:
        health_check_mode()

    if args.config_validate:
        config_path = resolve_config_path(args)
        validate_config_mode(config_path)
        sys.exit(0)

    if args.config_init:
        init_config_mode(force=args.force)
        sys.exit(0)

    if args.benchmark:
        config = load_config(resolve_config_path(args))
        benchmark_mode(config)
        sys.exit(0)

    if args.schedule:
        schedule_sleep(args.schedule)

    global LOG_LEVEL, LOG_FILE
    if args.log_file:
        LOG_FILE = args.log_file
    if args.quiet:
        LOG_LEVEL = 0
    elif args.verbose:
        LOG_LEVEL = 2

    if args.stop:
        pid = read_pid()
        if pid and is_running(pid):
            os.kill(pid, signal.SIGTERM)
            log(f"Stopped cascade-loop (PID {pid}).", color=Colors.GREEN)
            remove_pid()
        else:
            log("Not running.", color=Colors.YELLOW)
            remove_pid()
        sys.exit(0)

    if args.status:
        pid = read_pid()
        if pid and is_running(pid):
            log(f"Running (PID {pid}).", color=Colors.GREEN)
        else:
            log("Not running.", color=Colors.YELLOW)
            remove_pid()
        sys.exit(0)

    if args.list_profiles:
        profiles = list_profiles()
        if profiles:
            log("Available profiles:", color=Colors.CYAN + Colors.BOLD)
            for p in profiles:
                log(f"  - {p}", color=Colors.CYAN)
        else:
            log("No profiles found.", color=Colors.YELLOW)
        sys.exit(0)

    if args.watch:
        watch_mode()
        sys.exit(0)

    if args.simulate:
        simulate_mode()
        sys.exit(0)

    if args.config and args.profile:
        log("ERROR: --config and --profile are mutually exclusive.", color=Colors.RED)
        sys.exit(1)

    config = load_config(config_path=args.config, profile=args.profile)
    active_config_path = args.config or str(DEFAULT_CONFIG_PATH)

    if args.daemon:
        preflight_checks(config)
        daemonize(config, config_path=active_config_path, window_index=args.window_index, sound_file=args.sound_file, retry=args.retry, max_total_time=args.max_total_time, no_focus=args.no_focus)
        sys.exit(0)

    # Default: foreground
    preflight_checks(config)
    try:
        run_loop(
            config,
            config_path=active_config_path,
            dry_run=args.dry_run,
            window_index=args.window_index,
            sound_file=args.sound_file,
            retry=args.retry,
            max_total_time=args.max_total_time,
            no_focus=args.no_focus,
        )
    except KeyboardInterrupt:
        log("Interrupted by user.", color=Colors.YELLOW)
        sys.exit(0)

    # Post-loop reporting
    if args.report_file:
        write_report_file(args.report_file)
    if args.report:
        if JSON_LOG.exists():
            try:
                with open(JSON_LOG, "r") as f:
                    records = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log(f"Cannot read iterations.json for report: {e}", color=Colors.RED)
                records = []
        else:
            records = []
        if records:
            headers = list(records[0].keys())
            rows = []
            for r in records:
                cells = "".join(f"<td>{r.get(h, '')}</td>" for h in headers)
                rows.append(f"<tr>{cells}</tr>")
            header_row = "".join(f"<th>{h}</th>" for h in headers)
            html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Iteration Report</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left}}
th{{background:#f4f4f4}}tr:nth-child(even){{background:#fafafa}}</style>
</head><body><h1>Iteration Report</h1>
<table><thead><tr>{header_row}</tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>Total: {len(records)} iterations</p></body></html>"""
            send_report(args.report, html)
        else:
            log("No iteration data to email.", color=Colors.YELLOW)

    if args.webhook:
        send_webhook(args.webhook, headers_json=args.webhook_headers)


if __name__ == "__main__":
    main()
