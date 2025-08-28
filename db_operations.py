"""Database operations for the Streamlit Expense Tracker app using Supabase."""

from __future__ import annotations

import os
from datetime import datetime, date
from typing import List, Optional

import pandas as pd
from supabase import Client, create_client


def get_connection(url: str | None = None, key: str | None = None) -> Client:
    """Return a Supabase client.

    Parameters
    ----------
    url: str | None
        Supabase project URL. If not provided, the environment variable
        ``SUPABASE_URL`` is used.
    key: str | None
        Supabase API key. If not provided, the environment variable
        ``SUPABASE_KEY`` is used.
    """
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not provided")
    return create_client(url, key)


def init_db(conn: Client) -> None:
    """Ensure required tables are available in Supabase.

    Supabase tables are typically managed outside the application. This
    function performs a lightweight check so the rest of the code can assume
    the tables exist.
    """

    for table in ("categories", "expenses"):
        try:
            conn.table(table).select("id").limit(1).execute()
        except Exception:
            # If the table does not exist or cannot be queried, ignore the
            # error and allow Supabase to surface it later during operations.
            pass


def add_category(conn: Client, name: str) -> bool:
    """Insert a new category in uppercase if it does not already exist."""

    name = name.upper()
    try:
        conn.table("categories").insert({"name": name}).execute()
        return True
    except Exception:
        # A uniqueness violation (or any other error) results in False to
        # mirror the previous behaviour.
        return False


def get_categories(conn: Client) -> List[str]:
    """Return a list of existing categories sorted alphabetically."""

    resp = conn.table("categories").select("name").order("name").execute()
    return [row["name"] for row in resp.data or []]


def add_expense(
    conn: Client,
    amount: float,
    category: str,
    expense_date: date,
    receipt_url: Optional[str],
) -> None:
    """Insert a new expense into the database."""

    result = (
        conn.table("categories")
        .select("id")
        .eq("name", category.upper())
        .single()
        .execute()
    )
    if not result.data:
        raise ValueError("Category does not exist.")
    category_id = result.data["id"]
    conn.table("expenses").insert(
        {
            "amount": amount,
            "category_id": category_id,
            "date": expense_date.isoformat(),
            "receipt_url": receipt_url,
        }
    ).execute()


def get_month_totals(conn: Client) -> pd.DataFrame:
    """Return a DataFrame with months and their total expenses."""

    resp = conn.table("expenses").select("date, amount").execute()
    df = pd.DataFrame(resp.data)
    if df.empty:
        return df
    df["ym"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
    grouped = df.groupby("ym")["amount"].sum().reset_index(name="total")
    grouped["month"] = grouped["ym"].apply(
        lambda x: datetime.strptime(x, "%Y-%m").strftime("%b-%y")
    )
    grouped.sort_values("ym", inplace=True)
    return grouped[["month", "total"]]


def get_expenses_by_month(conn: Client, month: str) -> pd.DataFrame:
    """Return expenses for a given month (MMM-YY)."""

    if not month:
        return pd.DataFrame(columns=["date", "category", "amount"])
    start = datetime.strptime(month, "%b-%y")
    end = (start.replace(day=28) + pd.offsets.MonthEnd(1)).to_pydatetime()
    resp = (
        conn.table("expenses")
        .select("date, amount, categories(name)")
        .gte("date", start.date().isoformat())
        .lt("date", end.date().isoformat())
        .order("date")
        .execute()
    )
    records = [
        {
            "date": r["date"],
            "category": r.get("categories", {}).get("name"),
            "amount": r["amount"],
        }
        for r in resp.data or []
    ]
    return pd.DataFrame(records)
