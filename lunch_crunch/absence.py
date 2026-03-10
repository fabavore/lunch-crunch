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

"""Reusable absence-grid widget.

Renders a month-scoped table of dates x children with checkboxes.
Used by both the regular absence page (weekdays) and the holiday-absence
page (school-holiday dates only).
"""

import calendar
from datetime import date

from nicegui import ui

from lunch_crunch.db import get_db
from lunch_crunch.common import get_children, get_closing_days
from lunch_crunch.filter import month_and_group_filter

def absence_grid(toggle_absence, get_days, get_absent, get_locked=lambda conn, year, month: {},
                 title="", help_lbl="", empty_lbl="", extra_btn=None) -> None:
    """Render the full absence grid UI component.

    Args:
        toggle_absence: ``(conn, child_id, date_str, absent) -> None`` -
                        called inside an open DB connection to persist a checkbox change.
        get_days:       ``(conn, year, month) -> list[date]`` -
                        returns the ordered list of dates to display as columns.
        get_absent:     ``(conn, year, month) -> set[tuple[int, str]]`` 
                        returns ``{(child_id, date_str), ...}`` of absent entries.
        get_locked:     ``(conn, year, month) -> set[tuple[int, str]]`` -
                        returns entries shown as locked (amber "—", not editable).
                        Defaults to an empty set.
        title:          Optional heading rendered above the filter bar.
        help_lbl:       Optional explanatory text below the heading.
        empty_lbl:      Message shown when ``get_days`` returns an empty list.
    """
    today = date.today()
    current = {"year": today.year, "month": today.month, "group": None}

    def has_data(year: int, month: int) -> bool:
        month_str = f"{year}-{month:02d}"
        _, last = calendar.monthrange(year, month)
        with get_db() as conn:
            return bool(get_children(conn, f"{month_str}-01", f"{month_str}-{last}", current["group"]))

    def _toggle_absence(child_id: int, date_str: str, absent: bool) -> None:
        with get_db() as conn:
            toggle_absence(conn, child_id, date_str, absent)
        rebuild()

    def rebuild() -> None:
        year, month = current["year"], current["month"]
        _, last = calendar.monthrange(year, month)
        month_str = f"{year}-{month:02d}"
        first_day = f"{month_str}-01"
        last_day  = f"{month_str}-{last:02d}"

        with get_db() as conn:
            children = get_children(conn, first_day, last_day, current["group"])
            closed   = get_closing_days(conn, year, month)
            days     = get_days(conn, year, month)

            absent   = get_absent(conn, year, month)
            locked   = get_locked(conn, year, month)

            order_sent_today = conn.execute(
                "SELECT 1 FROM order_log WHERE date = ?", (today.isoformat(),)
            ).fetchone() is not None

        gap_days = {d for d, prev in zip(days[1:], days) if (d - prev).days > 1}

        grid_container.clear()

        with grid_container:
            if not children:
                ui.label(
                    "Keine Kinder registriert - bitte unter Einstellungen -> Kinder hinzufügen."
                ).classes("text-sm text-gray-500")
                return
            if not days:
                ui.label(
                    empty_lbl if empty_lbl else "Keine Tage konfiguriert."
                ).classes("text-sm text-gray-500")
                return

            with ui.card():
                with ui.element("table").classes("border-collapse w-max"):
                    bd = "border border-gray-200"

                    # Header row
                    with ui.element("tr"):
                        ui.element("th")
                        for d in days:
                            d_str = d.isoformat()
                            is_closed = d_str in closed
                            week_sep = "border-l-2 border-l-gray-400" if d in gap_days else ""
                            bg = "bg-gray-100" if is_closed else ("bg-blue-50" if d == today else "")
                            with ui.element("th").classes(
                                f"{bd} {week_sep} {bg} min-w-12 text-center px-1 py-1.5 font-semibold"
                            ):
                                ui.label(d.strftime("%a")).classes(
                                    "text-[11px] " + ("text-gray-400" if is_closed else "text-gray-500")
                                )
                                ui.label(str(d.day)).classes(
                                    "text-[13px]" + (" text-gray-400" if is_closed else "")
                                )

                    # One row per child
                    for child in children:
                        with ui.element("tr"):
                            with ui.element("td").classes(
                                f"{bd} px-2 py-1 font-medium whitespace-nowrap sticky"
                            ):
                                ui.label(child["name"])
                            for d in days:
                                d_str = d.isoformat()
                                is_closed = d_str in closed
                                is_locked = (child["id"], d_str) in locked
                                is_past   = d < today or (d == today and order_sent_today)
                                week_sep = "border-l-2 border-l-gray-400" if d in gap_days else ""
                                bg = ("bg-gray-100" if is_closed
                                    else "bg-amber-100" if is_locked
                                    else "bg-blue-50" if d == today else "")
                                with ui.element("td").classes(
                                    f"{bd} {week_sep} {bg} p-1 text-center"
                                ):
                                    if is_closed:
                                        ui.label("—").classes("text-[12px] text-gray-400")
                                    elif is_locked:
                                        ui.label("—").classes("text-[12px] text-amber-600")
                                    else:
                                        checked = (child["id"], d_str) not in absent
                                        ui.checkbox(
                                            value=checked,
                                            on_change=lambda e, cid=child["id"], ds=d_str:
                                                _toggle_absence(cid, ds, absent=not e.value)
                                        ).props("dense" + (" disable" if is_past else ""))

                    # Totals row
                    with ui.element("tr"):
                        with ui.element("td").classes(
                            f"{bd} bg-gray-50 px-2 py-1 font-semibold whitespace-nowrap sticky"
                        ):
                            ui.label("Gesamt")
                        for d in days:
                            d_str = d.isoformat()
                            is_closed = d_str in closed
                            week_sep = "border-l-2 border-l-gray-400" if d in gap_days else ""
                            bg = "bg-gray-100" if is_closed else ("bg-blue-50" if d == today else "bg-gray-50")
                            with ui.element("td").classes(
                                f"{bd} {week_sep} {bg} text-center py-1.5 px-1"
                            ):
                                if is_closed:
                                    ui.label("—").classes("text-[12px] text-gray-400")
                                else:
                                    count = sum(
                                        1 for c in children
                                        if (c["id"], d_str) not in locked
                                        and (c["id"], d_str) not in absent
                                    )
                                    ui.label(str(count)).classes("text-[13px] font-semibold")

    with ui.column().classes("w-full"):
        if title:
            ui.label(title).classes("text-2xl font-semibold").style("font-family: Antropos;")
            ui.separator()
        if help_lbl:
            ui.label(help_lbl).classes("text-sm text-gray-500")

        # Month navigation + group filter
        month_and_group_filter(current, update=rebuild, has_data=has_data, extra_btn=extra_btn)

        grid_container = ui.column()

    rebuild()
