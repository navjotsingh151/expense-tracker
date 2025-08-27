"""UI components for the Streamlit Expense Tracker app."""

from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd
import streamlit as st

import db_operations
import google_drive_upload


def render_month_tiles(conn) -> Optional[str]:
    """Render scrollable month tiles and return the selected month."""
    months_df = db_operations.get_month_totals(conn)
    months = months_df["month"].tolist() if not months_df.empty else []
    totals = months_df["total"].tolist() if not months_df.empty else []
    if "selected_month" not in st.session_state:
        st.session_state["selected_month"] = (
            months[-1] if months else dt.datetime.now().strftime("%b-%y")
        )
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] {overflow-x: auto;}
        div[data-testid="column"] {min-width: 110px;}
        .month-tile button {width:100%; height:60px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(months) if months else 1)
    for i, (month, total) in enumerate(zip(months, totals)):
        with cols[i]:
            label = f"{month}\n${total:.2f}"
            if st.button(label, key=f"month_{month}"):
                st.session_state["selected_month"] = month
    return st.session_state.get("selected_month")


def add_expense_form(conn) -> None:
    """Render a modal form for adding a new expense."""
    with st.modal("Add Expense"):
        with st.form("expense_form", clear_on_submit=True):
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            categories = db_operations.get_categories(conn)
            category = st.selectbox("Category", categories)
            new_category = st.text_input("New Category (uppercase)")
            add_cat = st.form_submit_button("Add Category")
            if add_cat and new_category:
                added = db_operations.add_category(conn, new_category.strip().upper())
                if added:
                    st.success("Category added.")
                else:
                    st.warning("Category already exists.")
                st.experimental_rerun()
            date = st.date_input("Date of expense", dt.date.today())
            receipt = st.file_uploader(
                "Upload receipt", type=["png", "jpg", "jpeg", "pdf"]
            )
            submitted = st.form_submit_button("Save Expense")
            if submitted:
                receipt_id = None
                if receipt is not None:
                    receipt_id = google_drive_upload.upload_file(receipt, receipt.name)
                db_operations.add_expense(conn, amount, category, date, receipt_id)
                st.success("Expense added.")
                st.session_state["show_add_expense"] = False
                st.experimental_rerun()


def render_expense_table(df: pd.DataFrame) -> None:
    """Display an HTML table of expenses and the total for the month."""
    if df.empty:
        st.info("No expenses for this month.")
        return
    df_display = df.copy()
    df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%Y-%m-%d")
    st.markdown(df_display.to_html(index=False), unsafe_allow_html=True)
    total = df_display["amount"].sum()
    st.markdown(f"**Total: ${total:.2f}**")
