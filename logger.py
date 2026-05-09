"""
logger.py — Logs every script run to runs.log
Tracks: timestamp, script name, status, notes
"""

import os
import traceback
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs.log")
SEPARATOR = "─" * 72


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_start(script: str):
    """Call at the top of a script run."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{SEPARATOR}\n")
        f.write(f"[{_now()}]  START  →  {script}\n")


def log_step(step: str, status: str = "OK", detail: str = ""):
    """Log a step within a run. status: OK | WARN | FAIL"""
    tag = {"OK": "✓", "WARN": "!", "FAIL": "✗"}.get(status, "·")
    line = f"  {tag}  {step}"
    if detail:
        line += f"  —  {detail}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_end(script: str, success: bool = True, note: str = ""):
    """Call at the end of a script run."""
    status = "DONE" if success else "FAILED"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{_now()}]  {status}  ←  {script}")
        if note:
            f.write(f"  ({note})")
        f.write("\n")


def log_error(context: str, error: Exception):
    """Log an exception with traceback."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"  ✗  ERROR in {context}:\n")
        for line in traceback.format_exc().splitlines():
            f.write(f"      {line}\n")


def tail_log(n: int = 40):
    """Print last n lines of the log."""
    if not os.path.exists(LOG_FILE):
        print("  No log file found yet.")
        return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print("".join(lines[-n:]))


def rotate_log(max_days: int = 30):
    """
    Archive log entries older than max_days into runs_archive_YYYYMM.log.
    Keeps runs.log clean and readable.
    """
    if not os.path.exists(LOG_FILE):
        return

    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=max_days)
    keep_lines = []
    archive_lines = []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_block = []
    block_date = None

    for line in lines:
        # Detect timestamp lines like [2026-05-06 20:30:00]
        if line.startswith("[") and len(line) > 20:
            try:
                ts = datetime.strptime(line[1:20], "%Y-%m-%d %H:%M:%S")
                block_date = ts
            except Exception:
                pass
        current_block.append(line)

        if line.startswith("[") and "DONE" in line or "FAILED" in line:
            if block_date and block_date < cutoff:
                archive_lines.extend(current_block)
            else:
                keep_lines.extend(current_block)
            current_block = []
            block_date = None

    # Write remaining kept lines
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(keep_lines)

    # Archive old lines
    if archive_lines:
        archive_name = LOG_FILE.replace("runs.log", f"runs_archive_{cutoff.strftime('%Y%m')}.log")
        with open(archive_name, "a", encoding="utf-8") as f:
            f.writelines(archive_lines)
