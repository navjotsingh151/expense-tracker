"""Google Drive upload helper for the Streamlit Expense Tracker app."""

from __future__ import annotations

import io
import json
import os
from typing import Optional

import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


def upload_file(file, filename: str, folder_id: Optional[str] = None) -> Optional[str]:
    """Upload a file to Google Drive using service account credentials.

    Parameters
    ----------
    file: UploadedFile
        File-like object obtained from ``st.file_uploader``.
    filename: str
        Desired file name on Google Drive.
    folder_id: Optional[str]
        Destination folder ID if uploading to a specific folder.

    Returns
    -------
    Optional[str]
        The Google Drive file ID if upload succeeds, otherwise ``None``.
    """
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        st.error("Google Drive credentials not provided.")
        return None
    creds = Credentials.from_service_account_info(
        json.loads(creds_json), scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]
    media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype=file.type)
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return uploaded.get("id")
