"""
view_log.py — View recent run history.
Usage:
  python view_log.py          # Last 50 lines
  python view_log.py 100      # Last 100 lines
  python view_log.py today    # Today's runs only
"""

import sys
import os
from datetime import date
from logger import LOG_FILE

def run():
    if not os.path.exists(LOG_FILE):
        print("\n  No log file yet. Run any script first.\n")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    arg = sys.argv[1] if len(sys.argv) > 1 else "50"

    if arg == "today":
        today_str = date.today().strftime("%Y-%m-%d")
        lines = [l for l in lines if today_str in l or l.startswith("  ") or l.startswith("─")]
        # Keep only runs that have today's date
        filtered, keep = [], False
        for l in lines:
            if today_str in l:
                keep = True
            if l.startswith("─"):
                keep = False
            if keep:
                filtered.append(l)
        lines = filtered
    else:
        try:
            n = int(arg)
            lines = lines[-n:]
        except ValueError:
            lines = lines[-50:]

    print("".join(lines))

if __name__ == "__main__":
    run()
