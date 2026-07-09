import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(DB_DIR, "contact_submissions.sqlite3")


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0
    remaining: int = 0


@dataclass(frozen=True)
class BanResult:
    banned: bool
    retry_after_seconds: int = 0
    reason: str = ""


def init_db() -> None:
    """Run this EXACTLY ONCE at application startup, not per request."""
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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ip_bans (
                ip TEXT PRIMARY KEY,
                banned_until INTEGER NOT NULL,
                reason TEXT
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_burst_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                day_start INTEGER NOT NULL,
                count INTEGER NOT NULL,
                UNIQUE(ip, day_start)
            );
            """
        )
        # SQLite performance optimization for concurrent access
        conn.execute("PRAGMA journal_mode=WAL;")


def _current_window_start(window_seconds: int, now: float) -> int:
    return int(now // window_seconds) * int(window_seconds)


def _utc_day_start_epoch(now: float) -> int:
    day_seconds = 24 * 60 * 60
    return int(now // day_seconds) * day_seconds


def is_ip_banned(*, ip: str, now: Optional[float] = None) -> BanResult:
    now_ts = int(now if now is not None else time.time())
    
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT banned_until, reason FROM ip_bans WHERE ip = ?",
            (ip,),
        )
        row = cur.fetchone()
        if row is None:
            return BanResult(banned=False)

        banned_until, reason = int(row[0]), row[1] or ""
        if banned_until <= now_ts:
            conn.execute("DELETE FROM ip_bans WHERE ip = ?", (ip,))
            return BanResult(banned=False)

        return BanResult(
            banned=True,
            retry_after_seconds=max(0, banned_until - now_ts),
            reason=reason,
        )


def ban_ip(*, ip: str, banned_until: int, reason: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ip_bans (ip, banned_until, reason) VALUES (?, ?, ?)",
            (ip, int(banned_until), reason),
        )


def check_and_increment_rate_limit(
    *,
    key: str,
    window_seconds: int,
    max_requests: int,
    now: Optional[float] = None,
) -> RateLimitResult:
    """Fixed-window rate limiter utilizing SQLite UPSERT syntax."""
    current_time = now if now is not None else time.time()
    window_start = _current_window_start(window_seconds, current_time)
    current_ts = int(current_time)
    retry_after = max(0, (window_start + int(window_seconds)) - current_ts)

    with sqlite3.connect(DB_PATH) as conn:
        # Context manager handles BEGIN/COMMIT/ROLLBACK cleanly
        cur = conn.execute(
            "SELECT count FROM contact_rate_limits WHERE key = ? AND window_start = ?",
            (key, window_start),
        )
        row = cur.fetchone()
        existing = int(row[0]) if row else 0

        if existing >= max_requests:
            return RateLimitResult(allowed=False, retry_after_seconds=retry_after, remaining=0)

        # Upsert: Inserts or increments on conflict
        conn.execute(
            """
            INSERT INTO contact_rate_limits (key, window_start, count) 
            VALUES (?, ?, 1)
            ON CONFLICT(key, window_start) DO UPDATE SET count = count + 1
            """,
            (key, window_start),
        )
        
        return RateLimitResult(
            allowed=True,
            retry_after_seconds=0,
            remaining=max_requests - (existing + 1),
        )


def check_and_increment_daily_limit(*, ip: str, max_requests: int, now: Optional[float] = None) -> RateLimitResult:
    """Fixed calendar-day limit in UTC."""
    return check_and_increment_rate_limit(
        key=f"ip:{ip}:daily",
        window_seconds=24 * 60 * 60,
        max_requests=max_requests,
        now=now,
    )


def _increment_burst_violation_for_today(*, ip: str, now: Optional[float] = None) -> int:
    current_time = now if now is not None else time.time()
    day_start = _utc_day_start_epoch(current_time)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO contact_burst_violations (ip, day_start, count) 
            VALUES (?, ?, 1)
            ON CONFLICT(ip, day_start) DO UPDATE SET count = count + 1
            """,
            (ip, day_start),
        )
        
        cur = conn.execute(
            "SELECT count FROM contact_burst_violations WHERE ip = ? AND day_start = ?",
            (ip, day_start)
        )
        return int(cur.fetchone()[0])