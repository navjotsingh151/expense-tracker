"""Chart utilities for the Streamlit Expense Tracker app."""

from __future__ import annotations

import pandas as pd
import altair as alt
import streamlit as st


def plot_month_bar_chart(df: pd.DataFrame) -> None:
    """Render a bar chart for the provided monthly expense data.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing columns `date`, `category`, and `amount`.
    """
    if df.empty:
        st.info("No expenses for this month.")
        return
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("date:O", title="Date"),
            y=alt.Y("amount:Q", title="Amount"),
            color=alt.Color("category:N", title="Category"),
            xOffset="category:N",
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)
