# Expense Tracker

A modular Streamlit application for tracking expenses.

## Features
- Scrollable month tiles showing total expenses per month.
- Dynamic bar chart grouped by expense category.
- Add Expense form with Dropbox receipt upload.
- Supabase database backend.

## Running the App
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set Supabase credentials as environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

3. Start the application:
   ```bash
   streamlit run main.py
   ```
4. To enable Dropbox uploads, configure one of the following credential options
   in a `.env` file or as environment variables:

   - `DROPBOX_API_TOKEN` – a short-lived access token generated from the Dropbox
     App Console. It will expire after a few hours.
   - For automatic token refresh, set `DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY`,
     and `DROPBOX_APP_SECRET` obtained through the OAuth2 flow. The helper will
     refresh the access token transparently.

5. Optionally, set `DROPBOX_FOLDER_PATH` to the folder inside your app's Dropbox
   space where receipts should be saved. The upload helper returns a shareable
   link that is stored alongside each expense.

