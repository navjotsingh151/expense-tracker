# Expense Tracker

A modular Streamlit application for tracking expenses.

## Features
- Scrollable month tiles showing total expenses per month.
- Dynamic bar chart grouped by expense category.
- Add Expense form with Google Drive receipt upload.
- SQLite database backend.

## Running the App
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   streamlit run main.py
   ```
3. By default, data is stored in `expenses.db` in the project root.
4. To enable Google Drive uploads, provide credentials in one of two ways:
   - **Service account:** set `GOOGLE_SERVICE_ACCOUNT_JSON` to the JSON string
     or path for your service account credentials. The account must have access
     to a Shared Drive because it has no personal storage quota.
   - **OAuth user credentials:** set `GOOGLE_OAUTH_CLIENT_JSON` to the client
     secret JSON (or its path). A browser window will prompt for authorization
     on first run and store a token in `gdrive_token.json` (override with
     `GOOGLE_OAUTH_TOKEN_JSON`). The OAuth client must be created as a *Desktop
     app* in Google Cloud Console so it includes the default
     `http://localhost` redirect URI; otherwise Google will return a
     `redirect_uri_mismatch` error during authorization.
5. Optionally, set `GOOGLE_DRIVE_FOLDER_ID` to the folder where receipts should
   be saved. The upload helper returns a shareable link that is stored alongside
   each expense.

