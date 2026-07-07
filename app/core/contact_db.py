import os
import sqlite3
from datetime import datetime
from typing import Optional


DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(DB_DIR, "contact_submissions.sqlite3")


def _ensure_db() -> None:
    os.makedirs(DB_DIR, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def save_submission(
    *,
    name: str,
    email: str,
    message: str,
    subject: Optional[str] = None,
) -> int:
    """Persist a contact submission into local SQLite.

    Returns:
        Newly created row id.
    """

    _ensure_db()

    created_at = datetime.utcnow().isoformat() + "Z"

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO contact_submissions (name, email, subject, message, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, subject, message, created_at),
        )
        conn.commit()
        return int(cur.lastrowid)

