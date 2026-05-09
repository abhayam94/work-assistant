# =============================================================================
# WORK ASSISTANT — CONFIG
# Copy this file, fill in your values, and never commit the filled version.
# Add config.py to your .gitignore if you fork this repo.
# =============================================================================

# --- JIRA ---
JIRA_BASE_URL = "https://yourcompany.atlassian.net"
JIRA_EMAIL = "your.work@clientdomain.com"
JIRA_API_TOKEN = "YOUR_JIRA_API_TOKEN_HERE"   # https://id.atlassian.com → Security → API tokens
JIRA_TOKEN_EXPIRY = "YYYY-MM-DD"              # Update when you renew
JIRA_PROJECT_KEY = "PROJ"                     # e.g. GRWU, DEV, ENG

# --- GMAIL (OAuth — work/client account) ---
GMAIL_ACCOUNT = "your.work@clientdomain.com"
GMAIL_CREDENTIALS_FILE = "gmail_credentials.json"
GMAIL_TOKEN_FILE = "gmail_token.json"

# --- GOOGLE CALENDAR (same credentials as Gmail) ---
CALENDAR_TOKEN_FILE = "gmail_calendar_token.json"

# --- GOOGLE DRIVE (same credentials as Gmail) ---
DRIVE_ACCOUNT = "your.work@clientdomain.com"
DRIVE_CREDENTIALS_FILE = "gmail_credentials.json"
DRIVE_TOKEN_FILE = "gmail_drive_token.json"
DRIVE_FOLDER_NAME = "YourFolderName"          # Exact folder name in Google Drive root

# --- TIMESHEET ---
# Windows example: r"C:\Users\YOUR_NAME\Documents\Work\Timesheet.xlsx"
# Mac example:     "/Users/YOUR_NAME/Documents/Work/Timesheet.xlsx"
LOCAL_TIMESHEET_PATH = r"C:\Users\YOUR_NAME\Documents\Work\Timesheet.xlsx"

# --- DEFAULT WORK HOURS ---
DEFAULT_SIGN_IN  = "09:00"
DEFAULT_SIGN_OUT = "18:00"

# --- JIRA STATUS MAPS ---
# Dev tickets
DEV_STARTED_STATUSES = ["discovery", "in progress"]
DEV_END_STATUSES     = ["ready for testing", "validation", "waiting to go live"]
DEV_CLOSE_STATUSES   = ["done"]

# Bug tickets
BUG_STARTED_STATUSES = ["in development"]
BUG_END_STATUSES     = ["final review"]
BUG_CLOSE_STATUSES   = ["accepted by client", "cancelled", "published to prod"]

# Combined
ALL_STARTED_STATUSES = DEV_STARTED_STATUSES + BUG_STARTED_STATUSES
ALL_END_STATUSES     = DEV_END_STATUSES     + BUG_END_STATUSES
ALL_CLOSE_STATUSES   = DEV_CLOSE_STATUSES   + BUG_CLOSE_STATUSES

# --- GMAIL GROUPING ---
# First names of teammates — used to classify emails into TEAM group
TEAM_NAMES = ["teammate1", "teammate2", "teammate3", "manager1"]

# Sender keywords for meeting/recording detection
MEETING_SENDERS  = ["fathom", "calendar-notification", "calendar.google", "zoom", "meet"]
MEETING_SUBJECTS = ["invitation:", "updated invitation:", "accepted:", "ooo", "recap", "recording"]

# Sender keywords for Jira/Atlassian notifications
JIRA_SENDERS = ["atlassian", "jira"]

# Company update senders
COMPANY_SENDERS = ["yourcompany", "your company"]

# System/security senders
SYSTEM_SENDERS = ["google", "mail delivery", "mailer-daemon", "no-reply", "noreply"]
