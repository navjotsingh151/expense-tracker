# Expense Tracker

A modular Streamlit application for tracking expenses.

## Features
- Scrollable month tiles showing total expenses per month.
- Dynamic bar chart grouped by expense category.
- Add Expense form with Dropbox receipt upload.
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
4. To enable Dropbox uploads, set `DROPBOX_API_TOKEN` in a `.env` file or as an
   environment variable. The token can be generated from the Dropbox App Console.
5. Optionally, set `DROPBOX_FOLDER_PATH` to the folder inside your app's Dropbox
   space where receipts should be saved. The upload helper returns a shareable
   link that is stored alongside each expense.

