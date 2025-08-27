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
4. To enable Google Drive uploads, set the `GOOGLE_SERVICE_ACCOUNT_JSON`
   environment variable to either the JSON string of your service account
   credentials or a path to the `.json` file. A `.env` file is loaded
   automatically. Service accounts do not have personal Drive storage;
   add the account to a Shared Drive or use delegated OAuth for uploads.
5. Optionally, set `GOOGLE_DRIVE_FOLDER_ID` to the folder where receipts
   should be saved. The upload helper returns a shareable link that is stored
   alongside each expense.

