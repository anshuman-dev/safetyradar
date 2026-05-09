import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "papers.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            authors     TEXT,
            abstract    TEXT,
            url         TEXT,
            pdf_url     TEXT,
            source      TEXT,
            published   TEXT,
            categories  TEXT,
            tags        TEXT,
            summary     TEXT,
            fetched_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
