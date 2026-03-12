#   LunchCrunch: A Python desktop app to manage food ordering
#
#   Copyright (C) 2025  Fabian Sauer
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""SQLite database layer for Lunch Crunch.

DB_PATH points to ``lunch_crunch.db`` inside the platform-specific user data
directory (e.g. ``~/.local/share/lunch-crunch/`` on Linux,
``%LOCALAPPDATA%\\lunch-crunch\\lunch-crunch\\`` on Windows).

Typical usage::

    from lunch_crunch.db import db, init_db

    init_db()  # called once at startup

    with db() as conn:
        rows = conn.execute("SELECT * FROM children").fetchall()
"""

import logging
import sqlite3
from contextlib import contextmanager

from platformdirs import user_data_path

logger = logging.getLogger(__name__)

_DB_PATH = user_data_path("lunch-crunch", ensure_exists=True) / "lunch_crunch.db"


def get_connection() -> sqlite3.Connection:
    """Open and return a raw connection with row_factory and foreign keys enabled.

    Prefer the :func:`get_db` context manager for normal use — it handles commit,
    rollback, and close automatically.
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager that yields a committed-or-rolled-back connection.

    Commits on clean exit, rolls back on any exception, always closes the
    connection::

        with get_db() as conn:
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.error("Database transaction rolled back", exc_info=True)
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS children (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                group_name  TEXT    NOT NULL,
                notes       TEXT    NOT NULL DEFAULT '',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                archived_at TEXT
            );

            CREATE TABLE IF NOT EXISTS absence (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id    INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
                date        TEXT    NOT NULL,
                UNIQUE(child_id, date)
            );

            -- holiday_absence: per-child absence blocks
            CREATE TABLE IF NOT EXISTS holiday_absence (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id    INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
                date        TEXT    NOT NULL,
                note        TEXT    NOT NULL DEFAULT '',
                UNIQUE(child_id, date)
            );

            -- closing_days: kindergarten closures, no orders possible
            CREATE TABLE IF NOT EXISTS closing_days (
                date    TEXT PRIMARY KEY,
                note    TEXT NOT NULL DEFAULT ''
            );

            -- holidays: school holiday dates, per-child absence configurable
            CREATE TABLE IF NOT EXISTS holidays (
                date    TEXT PRIMARY KEY,
                note    TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS order_log (
                date    TEXT PRIMARY KEY,
                sent_at TEXT NOT NULL DEFAULT (datetime('now')),
                count   INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL DEFAULT ''
            );
        """)
