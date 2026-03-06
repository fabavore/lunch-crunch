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


_CONFIG_PATH = user_config_path("lunch-crunch", ensure_exists=True) / "config.toml"
LOG_PATH     = user_log_path("lunch-crunch", ensure_exists=True) / "app.log"

def get_groups() -> list[str]:
    try:
        with open(_CONFIG_PATH, "rb") as f:
            return tomllib.load(f).get("groups", [])
    except FileNotFoundError:
        return []


def get_setting(key: str, default: str = "") -> str:
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def save_setting(key: str, value: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )


def get_children(conn, active_after: date, active_before: date, group: str | None = None) -> list:
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


def header() -> None:
    with ui.header(elevated=True).classes('items-center px-4 gap-2 bg-pink-900/90'):
        ui.label('Mahlzeit').classes('text-white text-xl font-bold').style('font-family: Antropos;')
        ui.space()
        ui.button('Bestellung',    on_click=lambda: ui.navigate.to('/'),
                  icon='restaurant').props('flat color=white').style('font-family: Antropos;')
        ui.button('Einstellungen', on_click=lambda: ui.navigate.to('/settings'),
                  icon='settings').props('flat color=white').style('font-family: Antropos;')
