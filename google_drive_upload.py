"""Google Drive upload helper for the Streamlit Expense Tracker app."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

# Load variables defined in a local .env if present so users do not need to
# export them manually.
load_dotenv()


def _debug(msg: str) -> None:
    """Print and display a debug message."""
    print(msg)
    st.write(msg)


def upload_file(file, filename: str, folder_id: Optional[str] = None) -> Optional[str]:
    """Upload a file to Google Drive using service account credentials.

    Parameters
    ----------
    file: UploadedFile
        File-like object obtained from ``st.file_uploader``.
    filename: str
        Desired file name on Google Drive.
    folder_id: Optional[str]
        Destination folder ID if uploading to a specific folder. If not provided,
        the ``GOOGLE_DRIVE_FOLDER_ID`` environment variable will be used when
        available.

    Returns
    -------
    Optional[str]
        A shareable Drive URL if upload succeeds, otherwise ``None``.
    """
    _debug(f"DEBUG: Starting upload of {filename}")
    raw_creds = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_creds:
        print("ERROR: Google Drive credentials not provided.")
        st.error("Google Drive credentials not provided.")
        return None
    _debug("DEBUG: Loaded GOOGLE_SERVICE_ACCOUNT_JSON from environment")

    # ``GOOGLE_SERVICE_ACCOUNT_JSON`` can either contain a JSON string or a path
    # to a JSON file. Handle both for convenience.
    creds_dict: dict
    if Path(str(raw_creds)).is_file():
        _debug(f"DEBUG: Treating credentials as file path: {raw_creds}")
        try:
            creds_dict = json.loads(Path(str(raw_creds)).read_text())
        except OSError:
            print("ERROR: Could not read Google Drive credentials file.")
            st.error("Could not read Google Drive credentials file.")
            return None
    else:
        _debug("DEBUG: Parsing credentials as JSON string")
        try:
            creds_dict = json.loads(raw_creds)
        except json.JSONDecodeError:
            print("ERROR: Invalid Google Drive credentials JSON.")
            st.error("Invalid Google Drive credentials JSON.")
            return None

    _debug("DEBUG: Building Drive service client")
    creds = Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=creds)

    if folder_id is None:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    _debug(f"DEBUG: Using folder ID: {folder_id}")
    file_metadata = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]
    _debug(f"DEBUG: File metadata: {file_metadata}")
    media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype=file.type)

    try:
        _debug("DEBUG: Initiating upload request")
        uploaded = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        _debug(f"DEBUG: Upload response: {uploaded}")
    except HttpError as exc:  # pragma: no cover - network errors are not deterministic
        # Common 403 occurs when the service account is not part of a Shared Drive
        # and therefore has no available storage quota.
        _debug(f"DEBUG: Upload failed with error: {exc}")
        if exc.resp.status == 403 and b"storageQuotaExceeded" in exc.content:
            print(
                "ERROR: Service account lacks Drive storage. Add it to a Shared Drive or use delegated OAuth credentials."
            )
            st.error(
                "Service account lacks Drive storage. Add it to a Shared Drive or "
                "use delegated OAuth credentials."
            )
        else:
            print(f"ERROR: Failed to upload receipt: {exc}")
            st.error(f"Failed to upload receipt: {exc}")
        return None

    return uploaded.get("webViewLink")
