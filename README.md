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
2. Create a `.streamlit/secrets.toml` file with your credentials:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-supabase-key"

   # Optional Dropbox settings
   # DROPBOX_API_TOKEN = "..."
   # DROPBOX_REFRESH_TOKEN = "..."
   # DROPBOX_APP_KEY = "..."
   # DROPBOX_APP_SECRET = "..."
   # DROPBOX_FOLDER_PATH = "receipts"
   ```

3. Start the application:
   ```bash
   streamlit run main.py
   ```

The app reads credentials from Streamlit's secrets but will also fall back to
environment variables when running locally.

