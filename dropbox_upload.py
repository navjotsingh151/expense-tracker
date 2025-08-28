"""Dropbox upload helper for the Streamlit Expense Tracker app."""

from __future__ import annotations

import os
from typing import Optional

import dropbox
import streamlit as st
from dotenv import load_dotenv

# Load variables from a local .env if present so users do not need to export
# them manually.
load_dotenv()


def _debug(msg: str) -> None:
    """Print and display a debug message."""
    print(msg)
    st.write(msg)


def _get_client() -> Optional[dropbox.Dropbox]:
    """Create a Dropbox client using the API token from the environment."""
    token = os.getenv("DROPBOX_API_TOKEN")
    if not token:
        print("ERROR: Dropbox API token not provided.")
        st.error("Dropbox API token not provided.")
        return None
    return dropbox.Dropbox(token)


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
        ``DROPBOX_FOLDER_PATH`` environment variable is used when available.

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
        folder_path = os.getenv("DROPBOX_FOLDER_PATH", "")
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
    except dropbox.exceptions.ApiError as exc:
        _debug(f"DEBUG: Upload failed with error: {exc}")
        print(f"ERROR: Failed to upload receipt: {exc}")
        st.error(f"Failed to upload receipt: {exc}")
        return None
