"""
drive_client.py — Google Drive sync (personal account: abhayam94.1@gmail.com)
Uploads/updates the timesheet in the 'Work' folder.
Run setup_drive_auth.py once before using this.
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import DRIVE_CREDENTIALS_FILE, DRIVE_TOKEN_FILE, DRIVE_FOLDER_NAME, LOCAL_TIMESHEET_PATH

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_service():
    creds = None
    if os.path.exists(DRIVE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(DRIVE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(DRIVE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def _get_folder_id(service):
    results = service.files().list(
        q=f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = results.get("files", [])
    if not files:
        raise FileNotFoundError(f"Folder '{DRIVE_FOLDER_NAME}' not found in Drive.")
    return files[0]["id"]


def _find_existing_file(service, folder_id, filename):
    results = service.files().list(
        q=f"name='{filename}' and '{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def sync_timesheet():
    """Upload or update the timesheet in Drive > Work folder."""
    if not os.path.exists(LOCAL_TIMESHEET_PATH):
        raise FileNotFoundError(f"Local timesheet not found: {LOCAL_TIMESHEET_PATH}")

    service = _get_service()
    folder_id = _get_folder_id(service)
    filename = os.path.basename(LOCAL_TIMESHEET_PATH)
    existing_id = _find_existing_file(service, folder_id, filename)

    media = MediaFileUpload(
        LOCAL_TIMESHEET_PATH,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=True
    )

    if existing_id:
        service.files().update(fileId=existing_id, media_body=media).execute()
        print(f"  Updated '{filename}' in Drive/{DRIVE_FOLDER_NAME}")
    else:
        metadata = {"name": filename, "parents": [folder_id]}
        service.files().create(body=metadata, media_body=media, fields="id").execute()
        print(f"  Uploaded '{filename}' to Drive/{DRIVE_FOLDER_NAME}")
