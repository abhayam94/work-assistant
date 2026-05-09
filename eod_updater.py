"""
eod_updater.py — End-of-day update.
Run: python eod_updater.py

Steps:
  1. Ask: default hours (11:30–20:30) or custom?
  2. Ask: brief task summary for today
  3. Update In-Out + monthly sheet
  4. Update Tickets sheet (backfill + new tickets)
  5. Sync to Google Drive
"""

from colorama import init, Fore, Style
from datetime import date
from timesheet_updater import update_inout_sheet, update_tickets_sheet
from drive_client import sync_timesheet
from logger import log_start, log_step, log_end, log_error

init(autoreset=True)


def ask_hours():
    print(Fore.CYAN + "\n  ⏱  Work Hours")
    print(Fore.WHITE + "  Default: 11:30 → 20:30")
    choice = input(Fore.YELLOW + "  Use default? (y/n): ").strip().lower()

    if choice == "y":
        return "11:30", "20:30", 9.0
    else:
        sign_in = input(Fore.WHITE + "  Sign-in time (HH:MM): ").strip()
        sign_out = input(Fore.WHITE + "  Sign-out time (HH:MM): ").strip()
        try:
            h_in, m_in = map(int, sign_in.split(":"))
            h_out, m_out = map(int, sign_out.split(":"))
            hours = round(((h_out * 60 + m_out) - (h_in * 60 + m_in)) / 60, 2)
        except Exception:
            print(Fore.RED + "  Invalid time format. Using defaults.")
            return "11:30", "20:30", 9.0
        return sign_in, sign_out, hours


def ask_task_summary():
    print(Fore.CYAN + "\n  📝  Today's Task Summary")
    print(Fore.WHITE + Style.DIM + "  Brief description for the In-Out sheet (e.g. 'Tickets 605, 613')")
    summary = input(Fore.YELLOW + "  > ").strip()
    return summary if summary else f"Work on {date.today().strftime('%d %b')}"


def run():
    # Startup checks — config, file lock, backup, token expiry
    from startup_checks import run_all as startup
    startup(require_timesheet=True, make_backup_first=True)

    today = date.today().strftime("%A, %d %B %Y")
    print()
    print(Fore.CYAN + Style.BRIGHT + "  WORK ASSISTANT — End of Day Update")
    print(Fore.WHITE + Style.DIM + f"  {today}")
    print(Fore.WHITE + "─" * 60)

    sign_in, sign_out, hours = ask_hours()
    summary = ask_task_summary()

    print()
    print(Fore.WHITE + "─" * 60)
    print(Fore.CYAN + "\n  Running updates...\n")

    # Step 1: Update In-Out + monthly sheet
    print(Fore.WHITE + "  [1/3] Updating In-Out & monthly sheet...")
    try:
        update_inout_sheet(sign_in, sign_out, summary, hours)
    except Exception as e:
        log_step("In-Out & monthly sheet", "FAIL", str(e))
        log_error("update_inout_sheet", e)
        log_end("eod_updater", success=False)
        print(Fore.RED + f"  ✗ In-Out update failed: {e}")
        return

    # Step 2: Update Tickets sheet
    print(Fore.WHITE + "\n  [2/3] Syncing Tickets sheet from Jira...")
    try:
        update_tickets_sheet()
    except Exception as e:
        log_step("Tickets sheet", "FAIL", str(e))
        log_error("update_tickets_sheet", e)
        log_end("eod_updater", success=False)
        print(Fore.RED + f"  ✗ Tickets update failed: {e}")
        return

    # Step 3: Apply formatting
    print(Fore.WHITE + "\n  [3/4] Formatting sheets...")
    try:
        from format_sheets import apply_all_formatting
        apply_all_formatting()
    except Exception as e:
        log_step("Formatting", "WARN", str(e))
        print(Fore.RED + f"  ✗ Formatting failed: {e}")

    # Step 4: Sync to Drive
    print(Fore.WHITE + "\n  [4/4] Syncing to Google Drive...")
    try:
        sync_timesheet()
    except Exception as e:
        log_step("Drive sync", "FAIL", str(e))
        log_error("sync_timesheet", e)
        log_end("eod_updater", success=False)
        print(Fore.RED + f"  ✗ Drive sync failed: {e}")
        return

    print()
    print(Fore.WHITE + "─" * 60)
    log_end("eod_updater", success=True, note=f"{hours}h logged")
    # Rotate log if older entries exceed 30 days
    from logger import rotate_log
    rotate_log(max_days=30)
    print(Fore.GREEN + Style.BRIGHT + "\n  ✓ All done. Great work today! 🎉\n")
    print(Fore.WHITE + Style.DIM + f"  Hours logged: {sign_in} – {sign_out}  ({hours}h)")
    print(Fore.WHITE + Style.DIM + f"  Task: {summary}\n")


if __name__ == "__main__":
    run()
