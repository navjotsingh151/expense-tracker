"""UI components for the Streamlit Expense Tracker app."""

from __future__ import annotations

import datetime as dt
import re
from typing import Optional

import pandas as pd
import streamlit as st

import db_operations
import dropbox_upload


def _debug(msg: str) -> None:
    """Print and display a debug message."""
    print(msg)
    st.write(msg)


def _rerun() -> None:
    """Rerun the Streamlit app supporting legacy and new APIs."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover - legacy fallback
        st.experimental_rerun()

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
        div.month-container {min-width:110px; border:1px solid #ccc; border-radius:8px; padding:4px; margin-right:4px; box-shadow:0 2px 4px rgba(0,0,0,0.1); text-align:center;}
        div.month-container.selected {background-color:#e6f0ff; box-shadow:0 4px 6px rgba(0,0,0,0.2);}
        div.month-container .month-total {font-weight:bold; margin-bottom:4px;}
        div.month-container button {
            width:100%;
            height:40px;
            border:none;
            background:transparent;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(months) if months else 1)
    for i, (month, total) in enumerate(zip(months, totals)):
        sel = "selected" if month == st.session_state["selected_month"] else ""
        with cols[i]:
            st.markdown(f'<div class="month-container {sel}">', unsafe_allow_html=True)
            st.markdown(f'<div class="month-total">${total:.2f}</div>', unsafe_allow_html=True)
            if st.button(month, key=f"month_{month}"):
                st.session_state["selected_month"] = month
            st.markdown("</div>", unsafe_allow_html=True)
    return st.session_state.get("selected_month")


def add_expense_form(conn) -> None:
    """Render a form for adding a new expense."""
    st.subheader("Add Expense")
    with st.form("expense_form", clear_on_submit=True):
        amount_str: str = st.text_input(
            "Amount", value="", placeholder="Enter amount", key="amount_input"
        )
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
            _rerun()
        date = st.date_input("Date of expense", dt.date.today())
        receipt = st.file_uploader(
            "Upload receipt", type=["png", "jpg", "jpeg", "pdf"]
        )
        submitted = st.form_submit_button("Save Expense")
        cancel = st.form_submit_button("Cancel")
        if submitted:
            _debug("DEBUG: Save Expense clicked")
            try:
                cleaned = re.sub(r"[^0-9.]", "", amount_str)
                amount = float(cleaned)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                st.error("Please enter a valid amount greater than 0.")
            else:
                receipt_url = None
                if receipt is not None:
                    _debug(f"DEBUG: Uploading receipt {receipt.name}")
                    receipt_url = dropbox_upload.upload_file(receipt, receipt.name)
                    _debug(f"DEBUG: Receipt URL returned: {receipt_url}")
                db_operations.add_expense(conn, amount, category, date, receipt_url)
                _debug("DEBUG: Expense saved to database")
                st.success("Expense added.")
                st.session_state["show_add_expense"] = False
                _rerun()
        elif cancel:
            st.session_state["show_add_expense"] = False
            _rerun()


def render_expense_table(df: pd.DataFrame) -> None:
    """Display an HTML table of expenses and the total for the month."""
    if df.empty:
        st.info("No expenses for this month.")
        return
    df_display = df.copy()
    df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%Y-%m-%d")
    total = df_display["amount"].sum()
    df_display.columns = [col.title() for col in df_display.columns]
    st.markdown(
        """
        <style>
        table.expense-table {width: 100%; border-collapse: collapse;}
        table.expense-table th {background-color: #f0f2f6; text-align: left;}
        table.expense-table td, table.expense-table th {border: 1px solid #ddd; padding: 4px 8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        df_display.to_html(index=False, classes="expense-table"), unsafe_allow_html=True
    )
    st.markdown(f"**Total: ${total:.2f}**")
