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

from datetime import date

from nicegui import ui

from lunch_crunch.common import header
from lunch_crunch.absence import absence_grid


@ui.page("/holiday_absence")
def holiday_absence_page() -> None:
    """Route "/holiday_absence" - per-child presence grid for school-holiday dates."""
    header()

    def toggle_absence(conn, child_id: int, date_str: str, absent: bool) -> None:
        """Store absences: a row means the child is ABSENT on that date."""
        if absent:
            conn.execute(
                "INSERT OR IGNORE INTO holiday_absence (child_id, date) VALUES (?, ?)",
                (child_id, date_str),
            )
        else:
            conn.execute(
                "DELETE FROM holiday_absence WHERE child_id = ? AND date = ?",
                (child_id, date_str),
            )

    def get_days(conn, year, month) -> list:
        month_str = f"{year}-{month:02d}"
        return [
            date.fromisoformat(r["date"])
            for r in conn.execute(
                "SELECT date FROM holidays WHERE date LIKE ?",
                (f"{month_str}-%",),
            ).fetchall()
        ]

    def get_absent(conn, year, month) -> set:
        month_str = f"{year}-{month:02d}"
        return {
            (r["child_id"], r["date"])
            for r in conn.execute(
                "SELECT child_id, date FROM holiday_absence WHERE date LIKE ?",
                (f"{month_str}-%",),
            ).fetchall()
        }

    absence_grid(
        toggle_absence, get_days, get_absent,
        title="Ferienabfrage",
        help_lbl="Hier festlegen, welche Kinder an den Ferientagen anwesend sind. "
            "Nicht angehakt = abwesend (in der Essensbestellung geblockt).",
        empty_lbl="Keine Ferien enigetragen."
    )