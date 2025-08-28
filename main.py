"""Main entry point for the Streamlit Expense Tracker app."""

from __future__ import annotations

import streamlit as st

import charts
import db_operations
import ui_components


def main() -> None:
    """Run the Streamlit expense tracker application."""
    st.set_page_config(page_title="Expense Tracker - Inc", layout="wide")

    # Global button style for a subtle 3D effect
    st.markdown(
        """
        <style>
        .stButton>button {
            border-radius: 8px;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .stButton>button:active {
            box-shadow: 0 2px 3px rgba(0,0,0,0.2);
            transform: translateY(2px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<h1 style='text-align:center;'>Expense Tracker - Inc</h1>", unsafe_allow_html=True)

    conn = db_operations.get_connection()
    db_operations.init_db(conn)

    # Top-right Add Expense button
    header_cols = st.columns([5, 1])
    with header_cols[1]:
        st.markdown('<div class="add-expense-btn">', unsafe_allow_html=True)
        if st.button("Add Expense"):
            st.session_state["show_add_expense"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    # Month selection tiles
    selected_month = ui_components.render_month_tiles(conn)

    # Display modal form if triggered
    if st.session_state.get("show_add_expense"):
        ui_components.add_expense_form(conn)

    # Fetch and display data for the selected month
    monthly_df = db_operations.get_expenses_by_month(conn, selected_month)
    charts.plot_month_bar_chart(monthly_df)
    ui_components.render_expense_table(monthly_df)


if __name__ == "__main__":
    main()
