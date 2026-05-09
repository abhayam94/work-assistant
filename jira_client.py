"""
jira_client.py — Jira REST API wrapper
All Jira interactions go through this module.
"""

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from config import JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY
import api_client


def _auth():
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def _headers():
    return {"Accept": "application/json"}


def get_my_open_tickets():
    """Fetch all unresolved tickets assigned to current user, ordered by priority + due date."""
    jql = (
        f"project = {JIRA_PROJECT_KEY} "
        "AND assignee = currentUser() "
        "AND resolution = Unresolved "
        "AND status not in (\"Accepted by Client\", \"Final Review\") "
        "ORDER BY priority ASC, due ASC, created DESC"
    )
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    params = {
        "jql": jql,
        "maxResults": 10,
        "fields": "summary,status,priority,duedate,created,issuetype,labels,description"
    }
    resp = api_client.get(url, auth=_auth(), headers=_headers(), params=params,
                          label="get_my_open_tickets")
    return resp.json().get("issues", [])


def get_resolved_tickets_since(start_date="2025-12-01"):
    """Fetch all resolved tickets assigned to current user since start_date."""
    jql = (
        f"project = {JIRA_PROJECT_KEY} "
        "AND assignee = currentUser() "
        "AND resolution != Unresolved "
        f"AND created >= \"{start_date}\" "
        "ORDER BY created ASC"
    )
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "summary,status,priority,duedate,created,issuetype,labels,description"
    }
    resp = api_client.get(url, auth=_auth(), headers=_headers(), params=params,
                          label="get_resolved_tickets")
    return resp.json().get("issues", [])


def get_ticket_changelog(issue_key):
    """Fetch full changelog for a ticket to extract status transition dates."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    params = {"expand": "changelog", "fields": "summary,status,issuetype,duedate,created,labels,parent"}
    resp = api_client.get(url, auth=_auth(), headers=_headers(), params=params,
                          label=f"changelog:{issue_key}")
    return resp.json()


def get_ticket_url(issue_key):
    return f"{JIRA_BASE_URL}/browse/{issue_key}"


def extract_status_dates(changelog_data, started_statuses, end_statuses, close_statuses):
    """
    From a ticket's changelog, extract the LATEST date each status category was entered.
    Returns dict: {started_on, end_date, close_date} — all as date objects or None.
    """
    histories = changelog_data.get("changelog", {}).get("histories", [])

    started_on = None
    end_date = None
    close_date = None

    for history in histories:
        created_str = history.get("created", "")
        try:
            ts = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            date = ts.date()
        except Exception:
            continue

        for item in history.get("items", []):
            if item.get("field") != "status":
                continue
            to_status = (item.get("toString") or "").lower().strip()

            if to_status in started_statuses:
                # Keep latest
                if started_on is None or date > started_on:
                    started_on = date

            if to_status in end_statuses:
                if end_date is None or date > end_date:
                    end_date = date

            if to_status in close_statuses:
                if close_date is None or date > close_date:
                    close_date = date

    return {
        "started_on": started_on,
        "end_date": end_date,
        "close_date": close_date
    }


def get_report_name(issue_data):
    """
    Try to extract the report/client name from labels or parent ticket summary.
    Falls back to empty string — user fills manually.
    """
    fields = issue_data.get("fields", {})

    # Check labels first (e.g. label 'in-shape', 'pure-gym', 'enhance')
    labels = fields.get("labels", [])
    label_map = {
        "in-shape": "In-Shape",
        "inshape": "In-Shape",
        "pure-gym": "Pure Gym",
        "puregym": "Pure Gym",
        "enhance": "Enhance",
        "crunch": "Crunch",
        "ufc": "UFC",
    }
    for label in labels:
        key = label.lower().replace(" ", "-")
        if key in label_map:
            return label_map[key]

    # Check parent summary for clues
    parent = fields.get("parent", {})
    if parent:
        parent_summary = (parent.get("fields", {}).get("summary") or "").lower()
        for k, v in label_map.items():
            if k in parent_summary:
                return v

    return ""


def _extract_description_text(desc_field):
    """Extract plain text from Jira's Atlassian Document Format (ADF) description."""
    if not desc_field:
        return ""
    if isinstance(desc_field, str):
        return desc_field.strip()
    # ADF format — walk content nodes recursively
    texts = []
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("content", []):
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(desc_field)
    return " ".join(t.strip() for t in texts if t.strip())


def format_ticket_for_digest(issue):
    """Format a single ticket for morning digest display."""
    fields = issue.get("fields", {})
    key = issue.get("key", "")
    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "")
    due = fields.get("duedate") or "No due date"
    created = fields.get("created", "")[:10] if fields.get("created") else ""
    description = _extract_description_text(fields.get("description"))
    url = get_ticket_url(key)

    return {
        "key": key,
        "summary": summary,
        "status": status,
        "priority": priority,
        "due": due,
        "created": created,
        "description": description,
        "url": url
    }
