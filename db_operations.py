"""Database operations for the Streamlit Expense Tracker app."""

from __future__ import annotations

import sqlite3
from datetime import datetime, date
from typing import List, Optional

import pandas as pd


def get_connection(db_path: str = "expenses.db") -> sqlite3.Connection:
    """Return a connection to the SQLite database.

    Parameters
    ----------
    db_path: str
        Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create necessary tables if they do not exist."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            receipt_url TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """
    )
    conn.commit()


def add_category(conn: sqlite3.Connection, name: str) -> bool:
    """Insert a new category in uppercase if it does not already exist.

    Parameters
    ----------
    conn: sqlite3.Connection
        Active database connection.
    name: str
        Category name to add. It will be stored in uppercase.

    Returns
    -------
    bool
        True if the category was inserted, False if it already existed.
    """
    name = name.upper()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_categories(conn: sqlite3.Connection) -> List[str]:
    """Return a list of existing categories sorted alphabetically."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM categories ORDER BY name")
    rows = cur.fetchall()
    return [row["name"] for row in rows]


def add_expense(
    conn: sqlite3.Connection,
    amount: float,
    category: str,
    expense_date: date,
    receipt_url: Optional[str],
) -> None:
    """Insert a new expense into the database."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM categories WHERE name = ?", (category,))
    result = cur.fetchone()
    if result is None:
        raise ValueError("Category does not exist.")
    category_id = result["id"]
    cur.execute(
        """
        INSERT INTO expenses (amount, category_id, date, receipt_url)
        VALUES (?, ?, ?, ?)
        """,
        (amount, category_id, expense_date.isoformat(), receipt_url),
    )
    conn.commit()


def get_month_totals(conn: sqlite3.Connection) -> pd.DataFrame:
    """Return a DataFrame with months and their total expenses."""
    query = (
        """
        SELECT strftime('%Y-%m', date) AS ym, SUM(amount) AS total
        FROM expenses
        GROUP BY ym
        ORDER BY ym
        """
    )
    df = pd.read_sql(query, conn)
    if df.empty:
        return df
    df["month"] = df["ym"].apply(
        lambda x: datetime.strptime(x, "%Y-%m").strftime("%b-%y")
    )
    return df[["month", "total"]]


def get_expenses_by_month(conn: sqlite3.Connection, month: str) -> pd.DataFrame:
    """Return expenses for a given month (MMM-YY)."""
    if not month:
        return pd.DataFrame(columns=["date", "category", "amount"])
    start = datetime.strptime(month, "%b-%y")
    end = (start.replace(day=28) + pd.offsets.MonthEnd(1)).to_pydatetime()
    query = (
        """
        SELECT e.date, c.name AS category, e.amount
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE date >= ? AND date < ?
        ORDER BY date
        """
    )
    df = pd.read_sql(
        query, conn, params=(start.date().isoformat(), end.date().isoformat())
    )
    return df
