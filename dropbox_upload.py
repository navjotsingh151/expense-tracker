"""Dropbox upload helper for the Streamlit Expense Tracker app."""

from __future__ import annotations

import os
from typing import Optional

import dropbox
import streamlit as st

# Credentials are read from Streamlit's ``secrets.toml`` when running on
# Streamlit Cloud. Environment variables act as a fallback for local use.


def _debug(msg: str) -> None:
    """Print and display a debug message."""
    print(msg)
    st.write(msg)


def _get_client() -> Optional[dropbox.Dropbox]:
    """Create a Dropbox client from configuration.

    The helper prefers the refresh-token flow when ``DROPBOX_REFRESH_TOKEN`` and
    app credentials are available so short-lived access tokens can be refreshed
    automatically. As a fallback, a static ``DROPBOX_API_TOKEN`` may be used,
    though it will eventually expire. Credentials may be supplied via
    ``st.secrets`` or environment variables.
    """

    refresh_token = st.secrets.get("DROPBOX_REFRESH_TOKEN") or os.getenv(
        "DROPBOX_REFRESH_TOKEN"
    )
    app_key = st.secrets.get("DROPBOX_APP_KEY") or os.getenv("DROPBOX_APP_KEY")
    app_secret = st.secrets.get("DROPBOX_APP_SECRET") or os.getenv(
        "DROPBOX_APP_SECRET"
    )
    token = st.secrets.get("DROPBOX_API_TOKEN") or os.getenv("DROPBOX_API_TOKEN")

    if refresh_token and app_key and app_secret:
        try:
            return dropbox.Dropbox(
                oauth2_refresh_token=refresh_token,
                app_key=app_key,
                app_secret=app_secret,
            )
        except dropbox.exceptions.AuthError as exc:
            _debug(f"DEBUG: Failed to authenticate with refresh token: {exc}")
            st.error("Dropbox authentication failed. Check refresh token settings.")
            return None

    if token:
        return dropbox.Dropbox(token)

    _debug("DEBUG: No Dropbox credentials provided")
    st.error("Dropbox credentials not provided.")
    return None


def upload_file(file, filename: str, folder_path: Optional[str] = None) -> Optional[str]:
    """Upload a file to Dropbox and return a shareable link.

    Parameters
    ----------
    file: UploadedFile
        File-like object obtained from ``st.file_uploader``.
    filename: str
        Desired file name on Dropbox.
    folder_path: Optional[str]
        Destination folder path inside the app folder. If omitted, the
        ``DROPBOX_FOLDER_PATH`` secret or environment variable is used when
        available.

    Returns
    -------
    Optional[str]
        A shareable Dropbox URL if upload succeeds, otherwise ``None``.
    """
    _debug(f"DEBUG: Starting upload of {filename}")
    dbx = _get_client()
    if dbx is None:
        return None

    if folder_path is None:
        folder_path = st.secrets.get("DROPBOX_FOLDER_PATH") or os.getenv(
            "DROPBOX_FOLDER_PATH", ""
        )
    folder_path = folder_path.strip("/")
    path = f"/{folder_path}/{filename}" if folder_path else f"/{filename}"
    _debug(f"DEBUG: Upload path: {path}")

    try:
        dbx.files_upload(file.getvalue(), path, mode=dropbox.files.WriteMode("overwrite"))
        _debug("DEBUG: Upload successful, creating shared link")
        try:
            link = dbx.sharing_create_shared_link_with_settings(path).url
        except dropbox.exceptions.ApiError as exc:
            if exc.error.is_shared_link_already_exists():
                link = dbx.sharing_list_shared_links(path=path).links[0].url
            else:
                _debug(f"DEBUG: Failed to create shared link: {exc}")
                link = None
        _debug(f"DEBUG: Shared link: {link}")
        return link
    except dropbox.exceptions.AuthError as exc:
        _debug(f"DEBUG: Authentication failed during upload: {exc}")
        st.error("Dropbox authentication failed. Please reauthorize the app.")
        return None
    except dropbox.exceptions.ApiError as exc:
        _debug(f"DEBUG: Upload failed with error: {exc}")
        print(f"ERROR: Failed to upload receipt: {exc}")
        st.error(f"Failed to upload receipt: {exc}")
        return None
