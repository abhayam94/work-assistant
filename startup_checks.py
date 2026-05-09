"""
startup_checks.py — Run before any script does real work.
Checks: config validity, file accessibility, token expiry warning, next month pre-creation.
"""

import os
import sys
import json
from datetime import date, datetime, timedelta
from colorama import Fore, Style


def _fail(msg: str):
    print(Fore.RED + f"\n  ✗ STARTUP CHECK FAILED: {msg}")
    print(Fore.WHITE + Style.DIM + "  Fix the issue above and re-run.\n")
    sys.exit(1)


def _warn(msg: str):
    print(Fore.YELLOW + f"  ⚠  {msg}")


def _ok(msg: str):
    print(Fore.GREEN + f"  ✓  {msg}")


# ── 1. Config validation ──────────────────────────────────────────

def check_config():
    try:
        from config import (
            JIRA_API_TOKEN, JIRA_BASE_URL, JIRA_EMAIL,
            LOCAL_TIMESHEET_PATH, GMAIL_CREDENTIALS_FILE,
            DRIVE_CREDENTIALS_FILE, DRIVE_TOKEN_FILE
        )
    except ImportError as e:
        _fail(f"config.py missing or broken: {e}")

    from config import JIRA_API_TOKEN, LOCAL_TIMESHEET_PATH, GMAIL_CREDENTIALS_FILE

    if "YOUR_JIRA_API_TOKEN" in JIRA_API_TOKEN or not JIRA_API_TOKEN.strip():
        _fail("JIRA_API_TOKEN is not set in config.py")

    if "YOUR_USERNAME" in LOCAL_TIMESHEET_PATH or not LOCAL_TIMESHEET_PATH:
        _fail("LOCAL_TIMESHEET_PATH is not set in config.py")

    _ok("Config values look valid")


# ── 2. Timesheet file exists and is not locked ────────────────────

def check_timesheet():
    from config import LOCAL_TIMESHEET_PATH

    if not os.path.exists(LOCAL_TIMESHEET_PATH):
        _fail(f"Timesheet not found: {LOCAL_TIMESHEET_PATH}")

    # Try to open for writing — if Excel has it open, this fails
    try:
        with open(LOCAL_TIMESHEET_PATH, "a"):
            pass
        _ok("Timesheet file is accessible (not open in Excel)")
    except PermissionError:
        print(Fore.RED + "\n  ✗ Timesheet is open in Excel — please close it first.")
        print(Fore.YELLOW + "  Close Excel and press Enter to retry, or Ctrl+C to quit.")
        try:
            input()
            # Retry once
            try:
                with open(LOCAL_TIMESHEET_PATH, "a"):
                    pass
                _ok("Timesheet file is now accessible")
            except PermissionError:
                _fail("Still locked. Close Excel completely and re-run.")
        except KeyboardInterrupt:
            print()
            sys.exit(0)


# ── 3. Google auth token files exist ─────────────────────────────

def check_auth_tokens():
    from config import GMAIL_TOKEN_FILE, DRIVE_TOKEN_FILE, GMAIL_CREDENTIALS_FILE

    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
        _fail(f"Gmail credentials file not found: {GMAIL_CREDENTIALS_FILE}\n"
              "  Download from Google Cloud Console → APIs & Services → Credentials")

    if not os.path.exists(GMAIL_TOKEN_FILE):
        _warn("gmail_token.json not found — Gmail auth will be triggered on first use")
    else:
        _ok("Gmail token found")

    if not os.path.exists(DRIVE_TOKEN_FILE):
        _warn("gmail_drive_token.json not found — Drive auth will be triggered on first use")
    else:
        _ok("Drive token found")


# ── 4. Jira API token expiry warning ─────────────────────────────

def check_jira_token_expiry():
    """
    Warn 30 days before the known Jira token expiry date.
    Update JIRA_TOKEN_EXPIRY in config.py when you renew.
    """
    try:
        from config import JIRA_TOKEN_EXPIRY
        expiry = datetime.strptime(JIRA_TOKEN_EXPIRY, "%Y-%m-%d").date()
        days_left = (expiry - date.today()).days
        if days_left < 0:
            _fail(f"Jira API token EXPIRED on {expiry}. Renew at id.atlassian.com → Security → API tokens")
        elif days_left <= 30:
            _warn(f"Jira API token expires in {days_left} days ({expiry}). "
                  f"Renew at id.atlassian.com → Security → API tokens")
        else:
            _ok(f"Jira API token valid — expires {expiry} ({days_left} days)")
    except (ImportError, AttributeError):
        _warn("JIRA_TOKEN_EXPIRY not set in config.py — add it to get expiry warnings")


# ── 5. Next month pre-creation warning ───────────────────────────

def check_next_month_prep():
    """
    In the last 5 working days of the month, warn that next month sheet
    should be pre-created. Returns True if action is needed.
    """
    today = date.today()
    import calendar
    _, last_day = calendar.monthrange(today.year, today.month)
    month_end = date(today.year, today.month, last_day)

    # Count working days remaining
    working_days_left = 0
    d = today
    while d <= month_end:
        if d.weekday() < 5:
            working_days_left += 1
        d += timedelta(days=1)

    if working_days_left <= 5:
        next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        next_name = next_month.strftime("%b %y")
        _warn(f"Only {working_days_left} working days left this month. "
              f"Run: python format_sheets.py --next to pre-create {next_name} sheet")
        return True
    return False


# ── 6. Rolling backup ─────────────────────────────────────────────

def make_backup():
    """
    Create a timestamped backup of the timesheet.
    Keep only the last 5 backups — delete older ones.
    """
    from config import LOCAL_TIMESHEET_PATH
    import shutil

    folder = os.path.dirname(LOCAL_TIMESHEET_PATH)
    backup_dir = os.path.join(folder, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"Timesheet_backup_{timestamp}.xlsx"
    backup_path = os.path.join(backup_dir, backup_name)

    shutil.copy2(LOCAL_TIMESHEET_PATH, backup_path)

    # Delete old backups — keep last 5
    backups = sorted([
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.startswith("Timesheet_backup_") and f.endswith(".xlsx")
    ])
    while len(backups) > 5:
        os.remove(backups.pop(0))

    _ok(f"Backup created: backups/{backup_name} (keeping last 5)")
    return backup_path


# ── Main entry ────────────────────────────────────────────────────

def run_all(require_timesheet: bool = True, make_backup_first: bool = False):
    """
    Run all startup checks.
    require_timesheet: False for morning_digest (doesn't touch the file)
    make_backup_first: True for eod_updater (writes to file)
    """
    check_config()
    check_jira_token_expiry()
    check_auth_tokens()
    check_next_month_prep()

    if require_timesheet:
        check_timesheet()

    if make_backup_first:
        make_backup()
