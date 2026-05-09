"""
morning_digest.py — Your work day briefing.
Run: python morning_digest.py
Style: Variation 2 — midnight blue, cyan pops, grouped Gmail, Calendar cards
"""

import textwrap, requests
from colorama import init, Fore, Back, Style
from jira_client import get_my_open_tickets, format_ticket_for_digest
from gmail_client import get_grouped_emails
from calendar_client import get_todays_meetings
from datetime import date
from logger import log_start, log_step, log_end, log_error

init(autoreset=True)

# ── Colour palette ────────────────────────────────────────────────
C  = "\033[38;5;39m"    # Cyan accent
CB = "\033[38;5;45m"    # Bright cyan
W  = "\033[38;5;252m"   # Soft white
DW = "\033[38;5;240m"   # Dim white / muted
B  = "\033[38;5;27m"    # Blue
PU = "\033[38;5;135m"   # Purple (calendar alt)
R  = "\033[38;5;203m"   # Red (highest)
OR = "\033[38;5;215m"   # Orange (high)
YE = "\033[38;5;227m"   # Yellow (medium)
GR = "\033[38;5;114m"   # Green
RS = Style.RESET_ALL

PRIORITY_COLORS = {
    "Highest": R,
    "High":    OR,
    "Medium":  YE,
    "Low":     GR,
    "Lowest":  DW,
}

WIDTH = 72


def _div(char="━", color=DW):
    print(color + char * WIDTH + RS)


def _section(label, count_str=""):
    print()
    side = (WIDTH - len(label) - 2) // 2
    right_side = WIDTH - len(label) - 2 - side
    suffix = f"  {count_str}" if count_str else ""
    print(f"{C}{'─' * side}{RS} {CB}{label}{RS} {C}{'─' * (right_side - len(suffix))}{RS}{DW}{suffix}{RS}")
    print()


def _header():
    print()
    print(DW + "━" * WIDTH + RS)
    print(CB + "  ◈  WORK ASSISTANT  ◈  MORNING DIGEST".center(WIDTH) + RS)
    today = date.today().strftime("%A, %d %B %Y").upper()
    print(DW + today.center(WIDTH) + RS)
    print(DW + "━" * WIDTH + RS)


def summarize_ticket(ticket):
    prompt = (
        f"Ticket: {ticket['key']}\nTitle: {ticket['summary']}\n"
        f"Status: {ticket['status']} | Priority: {ticket['priority']} | Due: {ticket['due']}\n"
        f"Description: {ticket['description'] or 'No description.'}\n\n"
        "Summarise this work ticket in 50-100 words. "
        "Be clear and a little casual — like a smart colleague catching you up before standup. "
        "Cover what the issue is, what needs doing, and any important context. No bullet points."
    )
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 300,
                  "messages": [{"role": "user", "content": prompt}]}
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception:
        desc = ticket["description"]
        return textwrap.fill(desc[:600], WIDTH) if desc else ticket["summary"]


def _hyperlink(text, url):
    """ANSI OSC 8 hyperlink — clickable in Windows Terminal."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


# Box geometry:
# Terminal line: "  │" + [INNER content = INNER chars wide] + "│"
# Total visual:   2  + 1 + INNER + 1 = INNER + 4
# We set WIDTH = total visual line width
# So INNER = WIDTH - 4
INNER = WIDTH - 4   # usable chars inside the box


def _row(visible_text, ansi_text=None):
    """
    Print one box row. Uses absolute cursor positioning for right border
    so it always lands at column WIDTH regardless of ANSI codes.
    """
    if ansi_text is None:
        ansi_text = visible_text
    if len(visible_text) > INNER:
        visible_text = visible_text[:INNER]
        ansi_text = visible_text
    # Move cursor to column WIDTH to place right border absolutely
    print(f"{DW}  │{RS}{ansi_text}\033[{WIDTH}G{DW}│{RS}")


def _box_top():
    print(f"{DW}  ┌{'─' * INNER}┐{RS}")

def _box_mid():
    print(f"{DW}  ├{'·' * INNER}\033[{WIDTH}G{DW}┤{RS}")

def _box_bot():
    print(f"{DW}  └{'─' * INNER}┘{RS}")


def print_ticket(i, t):
    pcolor  = PRIORITY_COLORS.get(t["priority"], W)
    due_col = R if t["due"] == "No due date" else YE
    key_link = _hyperlink(t["key"], t["url"])

    # Row 1 — visible: "#1   GRWU-607   HIGHEST    Blocked"
    num   = f"#{i:<4}"
    key_v = f"{t['key']:<13}"
    pri_v = f"{t['priority'].upper():<11}"
    sta_v = t["status"]
    row1_vis  = f" {num}{key_v}{pri_v}{sta_v}"
    row1_ansi = f" {DW}{num}{RS}{CB}{key_link}{RS}  {pcolor}{t['priority'].upper():<11}{RS}{DW}{sta_v}{RS}"

    # Title rows — wrap at INNER - 2 (1 space indent + 1 space before border)
    title_lines = textwrap.wrap(t["summary"], INNER - 2) or [t["summary"][:INNER - 2]]

    # Due row
    due_vis  = f" Due: {t['due']}"
    due_ansi = f" {DW}Due: {due_col}{t['due']}{RS}"

    _box_top()
    _row(row1_vis, row1_ansi)
    for tl in title_lines:
        _row(f" {tl}", f" {W}{tl}{RS}")
    _row(due_vis, due_ansi)
    _box_mid()

    print(f"{DW}  │{RS} {DW}Summarising...{RS}", end="\r")
    summary = summarize_ticket(t)
    for line in textwrap.wrap(summary, INNER - 2):
        _row(f" {line}", f" {DW}{line}{RS}")
    _box_bot()
    print()


def print_gmail(groups, recent_five):
    GROUP_LABELS = [
        ("team",     "TEAM",                 C),
        ("meetings", "MEETINGS & RECORDINGS", PU),
        ("jira",     "JIRA / ATLASSIAN",     B),
        ("company",  "COMPANY UPDATES",      GR),
        ("system",   "SYSTEM & SECURITY",    DW),
        ("other",    "OTHER",                W),
    ]

    total = sum(len(v) for v in groups.values())
    _section("GMAIL", f"{total} unread")

    for key, label, color in GROUP_LABELS:
        items = groups.get(key, [])
        if not items:
            continue
        print(f"  {DW}┌─ {color}{label}{DW} ({len(items)}){RS}")
        for e in items:
            sender = e["from"][:40]
            subj   = e["subject"][:60]
            print(f"  {DW}│{RS}  {W}{sender}{RS}")
            print(f"  {DW}│{RS}  {DW}  Subject: {subj}{RS}")
            if e["is_fathom"] and e["fathom_recap"]:
                # Single line recap for Fathom
                recap = e["fathom_recap"][:WIDTH - 12]
                print(f"  {DW}│{RS}     {PU}↳ {recap}{RS}")
            print(f"  {DW}│{RS}")
        print(f"  {DW}└{'─' * (WIDTH - 4)}{RS}")
        print()

    # Last 5 — full AI summary wrapped across lines, no truncation
    print(f"  {CB}◈ Last 5 emails{RS}")
    print()
    for e in recent_five:
        s = e.get("fathom_recap") or e.get("summary") or ""
        s_clean = s.replace("\n", " ").strip()
        print(f"  {C}{e['from'][:40]}{RS}")
        print(f"  {DW}  Subject: {e['subject'][:60]}{RS}")
        if s_clean:
            for line in textwrap.wrap(s_clean, WIDTH - 6):
                print(f"  {DW}  {line}{RS}")
        print()


def print_calendar(meetings):
    _section("CALENDAR", f"{len(meetings)} meeting{'s' if len(meetings) != 1 else ''} today")
    if not meetings:
        print(f"  {GR}  No meetings. Your calendar is blissfully empty.{RS}\n")
        return

    # Two-column card grid
    pairs = [meetings[i:i+2] for i in range(0, len(meetings), 2)]
    for pair in pairs:
        cards = []
        for m in pair:
            dur = f"{m['duration_min']}min"
            platform = f" · {m['platform']}" if m["platform"] else ""
            attendees = f" · {m['attendees']} others" if m["attendees"] else ""
            cards.append({
                "time": m["start"],
                "title": m["title"][:28],
                "meta": f"{dur}{platform}{attendees}"
            })
        if len(cards) == 2:
            t1, t2 = cards
            print(f"  {DW}┌{'─'*31}┬{'─'*31}┐{RS}")
            print(f"  {DW}│{RS}  {CB}{t1['time']:<29}{DW}│{RS}  {PU}{t2['time']:<29}{DW}│{RS}")
            print(f"  {DW}│{RS}  {W}{t1['title']:<29}{DW}│{RS}  {W}{t2['title']:<29}{DW}│{RS}")
            print(f"  {DW}│{RS}  {DW}{t1['meta']:<29}{DW}│{RS}  {DW}{t2['meta']:<29}{DW}│{RS}")
            print(f"  {DW}└{'─'*31}┴{'─'*31}┘{RS}")
        else:
            t1 = cards[0]
            print(f"  {DW}┌{'─'*31}┐{RS}")
            print(f"  {DW}│{RS}  {CB}{t1['time']:<29}{DW}│{RS}")
            print(f"  {DW}│{RS}  {W}{t1['title']:<29}{DW}│{RS}")
            print(f"  {DW}│{RS}  {DW}{t1['meta']:<29}{DW}│{RS}")
            print(f"  {DW}└{'─'*31}┘{RS}")
        print()


def run():
    from startup_checks import run_all as startup
    startup(require_timesheet=False, make_backup_first=False)
    log_start("morning_digest")

    _header()

    # ── JIRA ─────────────────────────────────────────────────────
    try:
        tickets = get_my_open_tickets()
        _section("JIRA", "Top 7")
        if not tickets:
            print(f"  {GR}  Zero tickets. Rarest of mornings — enjoy it.{RS}\n")
        else:
            for i, issue in enumerate(tickets[:7], 1):
                print_ticket(i, format_ticket_for_digest(issue))
        log_step("Jira", "OK", f"{len(tickets)} tickets")
    except Exception as e:
        log_error("Jira fetch", e)
        print(f"  {R}  Could not fetch Jira tickets: {e}{RS}\n")

    # ── GMAIL ─────────────────────────────────────────────────────
    try:
        groups, recent_five = get_grouped_emails(max_results=20)
        print_gmail(groups, recent_five)
        total = sum(len(v) for v in groups.values())
        log_step("Gmail", "OK", f"{total} unread")
    except Exception as e:
        log_error("Gmail fetch", e)
        print(f"  {R}  Could not fetch emails: {e}{RS}\n")

    # ── CALENDAR ──────────────────────────────────────────────────
    try:
        meetings = get_todays_meetings()
        print_calendar(meetings)
        log_step("Calendar", "OK", f"{len(meetings)} meetings")
    except Exception as e:
        log_error("Calendar fetch", e)
        print(f"  {R}  Could not fetch calendar: {e}{RS}\n")

    # ── Footer ────────────────────────────────────────────────────
    print(DW + "━" * WIDTH + RS)
    print(CB + "  You're all caught up. Go build something great. ›".center(WIDTH) + RS)
    print(DW + "━" * WIDTH + RS)
    print()
    log_end("morning_digest")


if __name__ == "__main__":
    run()
