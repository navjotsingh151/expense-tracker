"""Google Drive upload helper for the Streamlit Expense Tracker app."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Optional, Any

import streamlit as st
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials as UserCreds
from google.oauth2.service_account import Credentials as ServiceCreds
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
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


def _build_drive_service() -> Optional[Any]:
    """Create a Google Drive service using either OAuth or service account creds.

    Returns
    -------
    Optional[Resource]
        Drive API service resource or ``None`` if credentials are missing.
    """
    # If OAuth client details are provided, prefer them so users with personal
    # Drives can authorize the upload.
    oauth_raw = os.getenv("GOOGLE_OAUTH_CLIENT_JSON")
    scopes = ["https://www.googleapis.com/auth/drive.file"]
    if oauth_raw:
        _debug("DEBUG: Using OAuth client credentials")
        token_path = os.getenv("GOOGLE_OAUTH_TOKEN_JSON", "gdrive_token.json")
        redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
        creds: Optional[UserCreds] = None
        if Path(token_path).exists():
            _debug(f"DEBUG: Loading OAuth token from {token_path}")
            creds = UserCreds.from_authorized_user_file(token_path, scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                _debug("DEBUG: Refreshing expired OAuth token")
                creds.refresh(Request())
            else:
                # Build flow depending on credential type. Web application
                # credentials require a fixed redirect URI that matches the
                # authorized URI in Google Cloud Console (e.g.,
                # http://localhost:8501).
                if Path(oauth_raw).is_file():
                    if redirect_uri:
                        flow = Flow.from_client_secrets_file(
                            oauth_raw, scopes=scopes, redirect_uri=redirect_uri
                        )
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            oauth_raw, scopes
                        )
                else:
                    if redirect_uri:
                        flow = Flow.from_client_config(
                            json.loads(oauth_raw), scopes=scopes, redirect_uri=redirect_uri
                        )
                    else:
                        flow = InstalledAppFlow.from_client_config(
                            json.loads(oauth_raw), scopes
                        )

                if redirect_uri:
                    if "oauth_flow" not in st.session_state:
                        auth_url, _ = flow.authorization_url(
                            access_type="offline", prompt="consent"
                        )
                        st.session_state["oauth_flow"] = flow
                        st.markdown(f"[Authorize Google Drive]({auth_url})")
                        st.stop()
                    else:
                        flow = st.session_state["oauth_flow"]
                        params = st.experimental_get_query_params()
                        if "code" not in params:
                            auth_url, _ = flow.authorization_url(
                                access_type="offline", prompt="consent"
                            )
                            st.markdown(f"[Authorize Google Drive]({auth_url})")
                            st.stop()
                        flow.fetch_token(code=params["code"][0])
                        creds = flow.credentials
                        Path(token_path).write_text(creds.to_json())
                        st.experimental_set_query_params()
                        del st.session_state["oauth_flow"]
                else:
                    try:
                        creds = flow.run_local_server(port=0)
                    except Exception as exc:  # pragma: no cover - network/browser errors
                        _debug(f"DEBUG: OAuth authorization failed: {exc}")
                        st.error(
                            "OAuth authorization failed. Set GOOGLE_OAUTH_REDIRECT_URI"
                            " to an authorized redirect (e.g., http://localhost:8501)"
                            " or use a desktop OAuth client.",
                        )
                        return None
                    Path(token_path).write_text(creds.to_json())
        return build("drive", "v3", credentials=creds)

    # Fallback to service account credentials.
    raw_service = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_service:
        print("ERROR: Google Drive credentials not provided.")
        st.error("Google Drive credentials not provided.")
        return None
    _debug("DEBUG: Loaded GOOGLE_SERVICE_ACCOUNT_JSON from environment")

    if Path(str(raw_service)).is_file():
        _debug(f"DEBUG: Treating credentials as file path: {raw_service}")
        try:
            creds_dict = json.loads(Path(str(raw_service)).read_text())
        except OSError:
            print("ERROR: Could not read Google Drive credentials file.")
            st.error("Could not read Google Drive credentials file.")
            return None
    else:
        _debug("DEBUG: Parsing credentials as JSON string")
        try:
            creds_dict = json.loads(raw_service)
        except json.JSONDecodeError:
            print("ERROR: Invalid Google Drive credentials JSON.")
            st.error("Invalid Google Drive credentials JSON.")
            return None

    creds = ServiceCreds.from_service_account_info(creds_dict, scopes=scopes)
    return build("drive", "v3", credentials=creds)


def upload_file(file, filename: str, folder_id: Optional[str] = None) -> Optional[str]:
    """Upload a file to Google Drive using available credentials.

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
    service = _build_drive_service()
    if service is None:
        return None

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
