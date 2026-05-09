"""
monthly_export.py — Export manager-ready monthly report.
Run: python monthly_export.py
     python monthly_export.py "Apr 26"   (specific month)

Produces a separate .xlsx with only In-Out + that month's sheet.
No Tickets tab included (that's your personal tracker).
"""

import sys
from colorama import init, Fore, Style
from timesheet_updater import export_monthly_report
from datetime import date

init(autoreset=True)
from logger import log_start, log_step, log_end, log_error


def run():
    month = None
    if len(sys.argv) > 1:
        month = " ".join(sys.argv[1:])
    else:
        default = date.today().strftime("%b %y")
        inp = input(
            Fore.YELLOW + f"  Month to export [{default}]: "
        ).strip()
        month = inp if inp else default

    log_start("monthly_export")
    print(Fore.CYAN + f"\n  Exporting report for: {month}...")
    try:
        path = export_monthly_report(month)
        if path:
            log_step("Export", "OK", path)
            log_end("monthly_export", success=True, note=month)
            print(Fore.GREEN + Style.BRIGHT + f"\n  ✓ Report saved: {path}")
            print(Fore.WHITE + Style.DIM + "  Send this file to your reporting manager.\n")
    except Exception as e:
        log_error("monthly_export", e)
        log_end("monthly_export", success=False)
        print(Fore.RED + f"  ✗ Export failed: {e}\n")


if __name__ == "__main__":
    run()
