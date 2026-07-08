import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple


DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(DB_DIR, "contact_submissions.sqlite3")


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0
    remaining: int = 0


def _ensure_db() -> None:
    os.makedirs(DB_DIR, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                window_start INTEGER NOT NULL,
                count INTEGER NOT NULL,
                UNIQUE(key, window_start)
            );
            """
        )
        conn.commit()


def _current_window_start(window_seconds: int, now: Optional[float] = None) -> int:
    if now is None:
        now = time.time()
    return int(now // window_seconds) * int(window_seconds)


def check_and_increment_rate_limit(
    *,
    key: str,
    window_seconds: int,
    max_requests: int,
    now: Optional[float] = None,
) -> RateLimitResult:
    """Fixed-window rate limiter backed by SQLite.

    - key: identity string (e.g., IP)
    - window_seconds: size of fixed window
    - max_requests: max allowed in each window
    """

    _ensure_db()
    if now is None:
        now = time.time()

    window_start = _current_window_start(window_seconds, now)
    current_ts = int(now)
    next_window_start = window_start + int(window_seconds)
    retry_after = max(0, next_window_start - current_ts)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = None

        # Transactional update
        conn.execute("BEGIN")
        try:
            cur = conn.execute(
                "SELECT count FROM contact_rate_limits WHERE key = ? AND window_start = ?",
                (key, window_start),
            )
            row = cur.fetchone()
            if row is None:
                # First hit in this window
                if 1 > max_requests:
                    conn.execute("ROLLBACK")
                    return RateLimitResult(allowed=False, retry_after_seconds=retry_after, remaining=0)

                conn.execute(
                    "INSERT INTO contact_rate_limits (key, window_start, count) VALUES (?, ?, ?)",
                    (key, window_start, 1),
                )
                conn.execute("COMMIT")
                return RateLimitResult(allowed=True, retry_after_seconds=0, remaining=max_requests - 1)

            existing = int(row[0])
            if existing >= max_requests:
                conn.execute("COMMIT")
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after, remaining=0)

            conn.execute(
                "UPDATE contact_rate_limits SET count = count + 1 WHERE key = ? AND window_start = ?",
                (key, window_start),
            )
            conn.execute("COMMIT")
            return RateLimitResult(allowed=True, retry_after_seconds=0, remaining=max_requests - (existing + 1))

        except Exception:
            conn.execute("ROLLBACK")
            raise

