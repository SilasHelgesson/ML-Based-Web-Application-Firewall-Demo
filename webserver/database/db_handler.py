"""SQLite access layer for the demo shop.

INTENTIONALLY VULNERABLE. Every query below interpolates user input straight
into SQL so the app can be attacked with sqlmap and the detector measured
against it. Each function notes which injection class it exposes.

The safe version of any of these is a parameterised query:

    db.execute("SELECT * FROM users WHERE username = ?", (username,))
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson


import sqlite3
from pathlib import Path

from flask import g

DB_PATH = Path(__file__).parent / "app.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.close()
    print(f"[db] initialised {DB_PATH}")


def ensure_db():
    if not DB_PATH.exists():
        init_db()


def query_user(username, password):
    """VULNERABLE: boolean-based blind injection on the login form."""
    db = get_db()
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (
        username, password,
    )
    return db.execute(query).fetchone()


def query_product(product_id):
    """VULNERABLE: boolean-based blind injection on the product lookup."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM products WHERE id = '%s'" % product_id
    ).fetchone()
    return dict(row) if row is not None else None


def query_products(category=None):
    """VULNERABLE: union-based injection on the category filter."""
    db = get_db()
    if category:
        rows = db.execute(
            "SELECT * FROM products WHERE category = '%s'" % category
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM products").fetchall()
    return [dict(r) for r in rows]


def query_comments(product_id):
    """VULNERABLE: injection on the comment listing."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM comments WHERE product_id = '%s' ORDER BY id DESC" % product_id
    ).fetchall()
    return [dict(r) for r in rows]


def add_comment(product_id, username, content):
    """VULNERABLE: second-order injection.

    `executescript` runs multiple statements, so a payload that closes the
    INSERT can append its own UPDATE -- the stored value is then rendered on a
    later page view (stored XSS chained off the injection).
    """
    db = get_db()
    query = (
        "INSERT INTO comments (product_id, username, content) "
        "VALUES ('%s', '%s', '%s')" % (product_id, username, content)
    )
    db.executescript(query)
    db.commit()
