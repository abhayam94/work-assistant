# Work Assistant

A personal AI-powered terminal assistant that briefs you every morning — Jira tickets, Gmail, and Calendar — and keeps your timesheet in sync automatically. Built with Python and Claude AI.

---

## What it does

```
python morning_digest.py   # Morning briefing — Jira + Gmail + Calendar
python eod_updater.py      # End of day — updates Excel timesheet + Drive sync
python weekly_summary.py   # Friday wrap-up — hours, tickets closed, comments
python monthly_export.py   # Month end — clean manager report (no personal tracker)
python format_sheets.py    # Format and pre-populate timesheet sheets
```

---

## Morning Digest

Pulls your top 7 Jira tickets (priority + due date order), summarises each in plain English using Claude AI, groups unread Gmail by category (Team / Meetings / Jira / Company / System), shows Fathom meeting recaps inline, and lists today's calendar meetings — all in a styled terminal UI.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
             ◈  WORK ASSISTANT  ◈  MORNING DIGEST
                    MONDAY, 11 MAY 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

──────────────── JIRA ─────────────────────────────────── Top 7

  ┌──────────────────────────────────────────────────────────────────────┐
  │ #1   PROJ-001    HIGHEST    Blocked                                  │
  │ Dashboard not showing correct data                                   │
  │ Due: 2026-05-15                                                      │
  ├······································································┤
  │ Data pipeline issue affecting live reporting across service lines.   │
  │ Needs investigation before client review on Friday.                  │
  └──────────────────────────────────────────────────────────────────────┘
```

---

## File Descriptions

### Entry Points — Commands you run daily

| File | Purpose |
|---|---|
| `morning_digest.py` | Your start-of-day briefing. Pulls top 7 Jira tickets with AI summaries, groups unread Gmail into categories, shows Fathom meeting recaps inline, and displays today's calendar meetings as cards. Run this first thing every morning. |
| `eod_updater.py` | End-of-day updater. Asks for your sign-in/sign-out times (default or custom), logs the day in your Excel timesheet, pulls ticket status changes from Jira changelog, and syncs the file to Google Drive. |
| `weekly_summary.py` | Friday wrap-up. Shows hours logged for the week, tickets closed or moved to review, still-open tickets, overdue items, and new Jira comments received on your tickets. |
| `monthly_export.py` | Month-end manager report. Exports a clean copy of your timesheet with only the In-Out sheet and current month's sheet — no personal Tickets tracker included. |
| `format_sheets.py` | Formats all timesheet sheets with consistent styling — alternating week colours, bold week-end borders, and pre-populated dates. Run once to reformat existing sheets, or with `--next` to pre-create next month. |
| `backfill_preview.py` | Read-only preview tool. Shows what Jira knows about each ticket in your sheet vs what's currently recorded — before you commit any changes. Safe to run anytime. |
| `migrate_tickets_sheet.py` | One-time migration script. Restructures an old Tickets sheet into the new column format. Creates a backup automatically before touching anything. Run once only. |
| `view_log.py` | View your run history log. Shows recent script runs, steps completed, and any errors. Use `python view_log.py today` for today only, or `python view_log.py 100` for last 100 lines. |

---

### API Clients — External service integrations

| File | Purpose |
|---|---|
| `jira_client.py` | Jira REST API wrapper. Handles fetching open tickets, resolved tickets, full changelogs for date extraction, and report/client name detection from labels. All Jira interactions go through here. |
| `gmail_client.py` | Gmail API wrapper with email grouping and AI summarisation. Classifies emails into categories (Team, Meetings, Jira, Company, System, Other) based on sender and subject rules defined in `config.py`. Fetches Fathom email bodies and summarises them via Claude API. |
| `calendar_client.py` | Google Calendar API wrapper. Fetches today's events, filters declined invites and all-day events, detects meeting platform (Zoom, Google Meet, Teams), and returns structured meeting data for the morning digest. |
| `drive_client.py` | Google Drive API wrapper. Finds your target folder by name and uploads or updates the timesheet file. Uses a separate OAuth token from Gmail so both can be authenticated independently. |
| `api_client.py` | Resilient HTTP client used by `jira_client.py`. Wraps all GET and POST requests with 3-attempt retry logic and exponential backoff — handles rate limits, timeouts, and server errors gracefully without crashing. |

---

### Core Logic — Under the hood

| File | Purpose |
|---|---|
| `timesheet_updater.py` | Core Excel read/write engine. Handles In-Out sheet updates, monthly sheet population, Tickets sheet backfill and new row creation, date extraction from Jira changelog, cycle time calculation, and month-end report export. |
| `startup_checks.py` | Runs before every script. Validates config values, checks the timesheet file isn't open in Excel (and prompts you to close it), verifies auth token files exist, warns if your Jira API token is expiring within 30 days, creates a rolling backup before any write operation, and flags if you're in the last 5 working days of the month. |
| `logger.py` | Logging engine used by all scripts. Writes timestamped start, step, and end entries to `runs.log`. Supports OK / WARN / FAIL status per step, full error tracebacks on failure, and automatic log rotation — archiving entries older than 30 days to keep the log readable. |
| `format_sheets.py` | Sheet formatting and pre-population engine. Applies consistent styling across all sheets — header colours, alternating week fills, bold week-end borders, date formatting — and pre-populates In-Out with weekday rows and monthly sheets with all calendar days, weekends marked. |

---

### Configuration

| File | Purpose |
|---|---|
| `config.py` | The only file you need to edit. Contains all credentials (Jira API token, file paths), OAuth file references, default work hours, Jira status mappings for dev and bug tickets, and Gmail grouping rules (team names, meeting sender keywords, company sender keywords). |
| `requirements.txt` | Python package dependencies. Install with `pip install -r requirements.txt`. |
| `.gitignore` | Excludes token files (`*.json`), Excel files (`*.xlsx`), logs, backups, and Python cache from version control. |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/work-assistant.git
cd work-assistant
pip install -r requirements.txt
```

### 2. Fill in config.py

```python
JIRA_BASE_URL    = "https://yourcompany.atlassian.net"
JIRA_EMAIL       = "your.work@clientdomain.com"
JIRA_API_TOKEN   = "your_token_here"
JIRA_PROJECT_KEY = "PROJ"
LOCAL_TIMESHEET_PATH = r"C:\Users\YOUR_NAME\Documents\Work\Timesheet.xlsx"
TEAM_NAMES = ["alice", "bob", "carol"]   # first names of teammates
```

Generate a Jira API token at: https://id.atlassian.com → Security → API tokens

### 3. Set up Google OAuth (Gmail + Calendar + Drive)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Gmail API**, **Google Calendar API**, **Google Drive API**
3. Go to **APIs & Services → Credentials → Create OAuth Client ID** (Desktop app)
4. Download JSON → rename to `gmail_credentials.json` → place in project folder
5. Add your work email as a test user under **OAuth consent screen**

First-time auth (opens browser):
```bash
python -c "from gmail_client import get_grouped_emails; print('Gmail OK')"
python -c "from calendar_client import get_todays_meetings; print('Calendar OK')"
python -c "from drive_client import sync_timesheet; print('Drive OK')"
```

### 4. Run

```bash
# Windows Terminal recommended (for full Unicode box drawing support)
chcp 65001
python morning_digest.py
```

---

## Quick Reference

```bash
# Daily
python morning_digest.py         # start of day
python eod_updater.py            # end of day

# Weekly / monthly
python weekly_summary.py         # Friday wrap-up
python monthly_export.py         # month-end manager report

# Maintenance
python format_sheets.py          # reformat all sheets
python format_sheets.py --next   # pre-create next month sheets
python view_log.py               # view recent run log
python view_log.py today         # today's runs only

# If auth breaks — delete token and re-auth
del gmail_token.json
del gmail_drive_token.json
del gmail_calendar_token.json
python -c "from gmail_client import get_grouped_emails; print('OK')"
```

---

## What it saves

- ~15 min every morning (Jira review + Gmail triage)
- ~15 min every evening (timesheet update + Drive sync)
- ~30 min at month end (manager report)
- Roughly **8–9 hours per month**

---

## Adapting to your workflow

- **Different Jira statuses** — update `DEV_STARTED_STATUSES`, `DEV_END_STATUSES` etc in `config.py`
- **Different email groups** — update `TEAM_NAMES`, `MEETING_SENDERS` in `config.py`
- **Mac** — change `LOCAL_TIMESHEET_PATH` to a Unix path, replace `del` with `rm` in auth reset commands
- **Different timesheet structure** — see `timesheet_updater.py` for column definitions

---

## Built with

- Python 3.10+
- Jira REST API · Gmail API · Google Calendar API · Google Drive API
- Claude API (Anthropic) — ticket and email summaries
- openpyxl — Excel read/write
- colorama — terminal colours

---

## License

MIT — use it, adapt it, make it yours.
