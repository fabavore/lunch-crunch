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

"""Reports page - monthly meal counts per child."""

import calendar
from datetime import date

from nicegui import ui

from lunch_crunch.db import get_db
from lunch_crunch.common import weekdays_of_month, get_children, get_closing_days, header
from lunch_crunch.filter import month_and_group_filter

@ui.page("/reports")
def reports_page() -> None:
    """Route "/reports" - monthly meal count summary and per-child breakdown."""
    header()

    today = date.today()
    current = {"year": today.year, "month": today.month, "group": None}
    is_forecast = True

    def has_data(year: int, month: int) -> bool:
        month_str = f"{year}-{month:02d}"
        _, last = calendar.monthrange(year, month)
        with get_db() as conn:
            return bool(get_children(conn, f"{month_str}-01", f"{month_str}-{last}", current["group"]))

    def export() -> None:
        None

    def build_download_btn() -> None:
        download_btn = ui.button("Exportieren", icon="download", on_click=export).props("flat dense")
        download_btn.set_enabled(not is_forecast)

    def rebuild() -> None:
        year, month = current["year"], current["month"]
        _, last = calendar.monthrange(year, month)
        month_str = f"{year}-{month:02d}"
        first_day = f"{month_str}-01"
        last_day  = f"{month_str}-{last:02d}"

        with get_db() as conn:
            children = get_children(conn, first_day, last_day, current["group"])
            closed   = get_closing_days(conn, year, month)
            days     = [d for d in weekdays_of_month(year, month) if d.isoformat() not in closed]

            absent   = {
                (r["child_id"], r["date"])
                for r in conn.execute(
                    "SELECT child_id, date FROM absence WHERE date LIKE ?",
                    (f"{month_str}-%",),
                ).fetchall()
            }
            holiday_absent = {
                (r["child_id"], r["date"])
                for r in conn.execute(
                    "SELECT child_id, date FROM holiday_absence WHERE date LIKE ?",
                    (f"{month_str}-%",),
                ).fetchall()
            }

        # Per-child meal counts
        child_counts = []
        grand_total = 0
        for child in children:
            meals = sum(
                1 for d in days
                if (child["id"], d.isoformat()) not in absent
                and (child["id"], d.isoformat()) not in holiday_absent
            )
            child_counts.append((child, meals))
            grand_total += meals

        is_forecast = (year, month) >= (today.year, today.month)

        # -- Summary card ------------------------------------------------------
        summary_card.clear()
        with summary_card:
            with ui.row().classes("items-center gap-2"):
                ui.label("Monatsübersicht").classes("font-medium")
                if is_forecast:
                    ui.badge("Prognose", color="orange").props("outline")
            ui.separator()
            with ui.row().classes("gap-8"):
                with ui.column().classes("gap-0 items-center"):
                    ui.label(str(len(days))).classes("text-3xl font-bold text-blue-600")
                    ui.label("Kindergartentage").classes("text-xs text-gray-500")
                with ui.column().classes("gap-0 items-center"):
                    ui.label(str(len(children))).classes("text-3xl font-bold text-blue-600")
                    ui.label("Kinder").classes("text-xs text-gray-500")
                with ui.column().classes("gap-0 items-center"):
                    ui.label(str(grand_total)).classes("text-3xl font-bold text-green-600")
                    ui.label(
                        "Essen erwartet" if is_forecast else "Essen bestellt"
                    ).classes("text-xs text-gray-500")

        # -- Per-child card ----------------------------------------------------
        children_card.clear()
        with children_card:
            ui.label("Essen pro Kind").classes("font-medium")
            ui.separator()
            if not children:
                ui.label("Keine Kinder registriert.").classes("text-gray-500 text-sm")
            else:
                ui.table(rows=[
                    {"name": child["name"], "group": child["group_name"], "meals": meals}
                    for child, meals in child_counts
                ], columns=[
                    {"name": "name", "label": "Name", "field": "name", "align": "left"},
                    {"name": "group", "label": "Gruppe", "field": "group", "align": "left"},
                    {
                        "name": "meals", 
                        "label": "Essen erwartet" if is_forecast else "Essen bestellt", 
                        "field": "meals", 
                        "align": "right"
                    },
                ]).classes("w-full")

    with ui.column().classes("w-full max-w-2xl mx-auto"):
        ui.label("Berichte").classes("text-2xl font-semibold").style("font-family: Antropos;")
        ui.separator()

        # Month navigation + group filter
        month_and_group_filter(
            current, update=rebuild, has_data=has_data, extra_btn=build_download_btn
        )

        summary_card = ui.card().classes("w-full")
        children_card = ui.card().classes("w-full")

    rebuild()
