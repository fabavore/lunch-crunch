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

"""Shared constants, helpers, and header for Lunch Crunch."""

import calendar
import tomllib
from datetime import date

from nicegui import ui
from platformdirs import user_config_path, user_log_path

from lunch_crunch.db import get_db


APP_NAME = "MahlZahl"

_CONFIG_PATH = user_config_path(APP_NAME.lower(), ensure_exists=True) / "config.toml"
LOG_PATH     = user_log_path(APP_NAME.lower(), ensure_exists=True) / "lunch_crunch.log"

DEFAULT_EMAIL_SUBJECT = "Mittagessen-Bestellung {Datum}"
DEFAULT_EMAIL_BODY = """Guten Morgen,\n\n
    die heutige Mittagessen-Bestellung: {Anzahl} Essen.\n\n
    Mit freundlichen Grüßen\n
    Euer Kindergarten-Team"""


def weekdays_of_month(year: int, month: int) -> list[date]:
    """Return all Mon-Fri dates in the given month."""
    _, last_day = calendar.monthrange(year, month)
    return [
        date(year, month, d)
        for d in range(1, last_day + 1)
        if date(year, month, d).weekday() < 5
    ]


def get_groups() -> list[str]:
    """Return the list of group names from the TOML config, or an empty list if not configured."""
    try:
        with open(_CONFIG_PATH, "rb") as f:
            return tomllib.load(f).get("groups", [])
    except FileNotFoundError:
        return []


def get_setting(key: str, default: str = "") -> str:
    """Return the value for *key* from the settings table, or *default* if missing."""
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def save_setting(key: str, value: str) -> None:
    """Upsert *key* -> *value* in the settings table."""
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )


def get_children(conn, active_after: date | str, active_before: date | str, group: str | None = None) -> list:
    """Return children active during [active_after, active_before], optionally filtered by group name."""
    if group:
        return conn.execute(
            "SELECT id, name, group_name FROM children "
            "WHERE DATE(created_at) <= ? AND (archived_at IS NULL OR DATE(archived_at) >= ?) "
            "AND group_name = ? ORDER BY name",
            (active_before, active_after, group),
        ).fetchall()
    return conn.execute(
        "SELECT id, name, group_name FROM children "
        "WHERE DATE(created_at) <= ? AND (archived_at IS NULL OR DATE(archived_at) >= ?) "
        "ORDER BY group_name, name",
        (active_before, active_after),
    ).fetchall()


def get_closing_days(conn, year, month) -> dict:
    """Return ``{date_str: note}`` for all closing days in the given month."""
    month_str = f"{year}-{month:02d}"
    return {
        r["date"]: r["note"]
            for r in conn.execute(
                "SELECT date, note FROM closing_days WHERE date LIKE ?",
                (f"{month_str}-%",),
            ).fetchall()
    }


def group_date_rows(rows) -> list:
    """Group consecutive date rows (same note, gap at most 3 days for weekends) into
    (from_str, to_str, note, [date_str, ...]) tuples."""
    groups = []
    if not rows:
        return groups

    row = rows[0]
    dates = [date.fromisoformat(row["date"])]
    note  = row["note"]

    for row in rows[1:]:
        dt = date.fromisoformat(row["date"])
        nt = row["note"]
        if ((dt - dates[-1]).days <= 1 or dt.weekday() == 0 and (dt - dates[-1]).days <= 3) and nt == note:
            dates.append(dt)
        else:
            groups.append((dates[0], dates[-1], note, dates))
            dates = [dt]
            note  = nt

    groups.append((dates[0], dates[-1], note, dates))
    return groups


def header() -> None:
    """Render the application top-bar with navigation buttons."""
    with ui.header(elevated=True).classes("items-center px-4 gap-2 bg-pink-900/90"):
        ui.label(APP_NAME).classes("text-white text-xl font-bold").style("font-family: Antropos;")
        ui.space()
        ui.button("Bestellung",    on_click=lambda: ui.navigate.to("/"),
                  icon="restaurant").props("flat color=white").style("font-family: Antropos;")
        ui.button("Ferienabfrage", on_click=lambda: ui.navigate.to("/holiday_absence"),
                  icon="event_busy").props("flat color=white").style("font-family: Antropos;")
        ui.button("Berichte", on_click=lambda: ui.navigate.to("/reports"),
                  icon="bar_chart").props("flat color=white").style("font-family: Antropos;")
        ui.button("Einstellungen", on_click=lambda: ui.navigate.to("/settings"),
                  icon="settings").props("flat color=white").style("font-family: Antropos;")
