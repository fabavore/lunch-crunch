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

import calendar
from datetime import date, timedelta

from nicegui import ui

from lunch_crunch.db import get_db
from lunch_crunch.common import get_groups, get_children, get_closing_days
from lunch_crunch.filter import month_and_group_filter

def absence_grid(toggle_absence, get_days, get_absent, get_locked=lambda conn, year, month: {}, 
                 title="", help_lbl="", empty_lbl="") -> None:
    today = date.today()
    current = {"year": today.year, "month": today.month, "group": None}

    def has_data(year: int, month: int) -> bool:
        month_str = f"{year}-{month:02d}"
        _, last = calendar.monthrange(year, month)
        with get_db() as conn:
            return bool(get_children(conn, f"{month_str}-01", f"{month_str}-{last}", current["group"]))

    with ui.column().classes("w-full"):
        if title:
            ui.label(title).classes("text-2xl font-semibold").style("font-family: Antropos;")
            ui.separator()
        if help_lbl:
            ui.label(help_lbl).classes("text-sm text-gray-500")

        # Month navigation + group filter
        month_and_group_filter(current, update=lambda: rebuild(), has_data=has_data)

        with ui.card():
            grid_container = ui.column()

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
                            is_past   = d < today
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

    rebuild()


# def absence_grid(get_days) -> None:
#     today = date.today()
#     current = {"year": today.year, "month": today.month, "group": None}

#     with ui.column().classes("w-full"):
#         # Month navigation + group filter
#         month_and_group_filter(current, update=lambda: rebuild())

#         with ui.card():
#             table_container = ui.column()

#     def toggle_absence(child_id: int, date_str: str, absent: bool) -> None:
#         """Store absences: a row means the child is ABSENT on that date."""
#         with get_db() as conn:
#             if absent:
#                 conn.execute(
#                     "INSERT OR IGNORE INTO absence (child_id, date) VALUES (?, ?)",
#                     (child_id, date_str),
#                 )
#             else:
#                 conn.execute(
#                     "DELETE FROM absence WHERE child_id = ? AND date = ?",
#                     (child_id, date_str),
#                 )
#         rebuild()

#     def rebuild() -> None:
#         year, month = current["year"], current["month"]
#         _, last = calendar.monthrange(year, month)
#         days      = [date(year, month, d) for d in range(1, last + 1) if date(year, month, d).weekday() < 5]
#         month_str = f"{year}-{month:02d}"
#         first_day = f"{month_str}-01"
#         last_day  = f"{month_str}-{last:02d}"

#         with get_db() as conn:
#             children = get_children(conn, first_day, last_day, current["group"])
#             absent = {
#                 (r["child_id"], r["date"])
#                 for r in conn.execute(
#                     "SELECT child_id, date FROM absence WHERE date LIKE ?",
#                     (f"{month_str}-%",),
#                 ).fetchall()
#             }
#             holiday_absent = {
#                 (r["child_id"], r["date"])
#                 for r in conn.execute(
#                     "SELECT child_id, date FROM holiday_absence WHERE date LIKE ?",
#                     (f"{month_str}-%",),
#                 ).fetchall()
#             }
#             closing_days = {
#                 r["date"]
#                 for r in conn.execute(
#                     "SELECT date FROM closing_days WHERE date LIKE ?",
#                     (f"{month_str}-%",),
#                 ).fetchall()
#             }

#         table_container.clear()

#         with table_container:
#             with ui.element("table").classes("border-collapse w-max"):
#                 bd = "border border-gray-200"

#                 # Header row
#                 with ui.element("tr"):
#                     ui.element("th")
#                     for d in days:
#                         d_str = d.isoformat()
#                         is_closing = d_str in closing_days
#                         bg = "bg-gray-100" if is_closing else ("bg-blue-50" if d == today else "")
#                         week_sep = "border-l-2 border-l-gray-400" if d.weekday() == 0 else ""
#                         with ui.element("th").classes(
#                             f"{bd} {week_sep} {bg} min-w-12 text-center px-1 py-1.5 font-semibold"
#                         ):
#                             ui.label(d.strftime("%a")).classes(
#                                 "text-[11px] " + ("text-gray-400" if is_closing else "text-gray-500")
#                             )
#                             ui.label(str(d.day)).classes(
#                                 "text-[13px]" + (" text-gray-400" if is_closing else "")
#                             )

#                 # One row per child
#                 for child in children:
#                     with ui.element("tr"):
#                         with ui.element("td").classes(f"{bd} px-2 py-1 font-medium whitespace-nowrap sticky"):
#                             ui.label(child["name"])
#                         for d in days:
#                             d_str = d.isoformat()
#                             is_closed = d_str in closing_days
#                             is_ha      = (child["id"], d_str) in holiday_absent
#                             is_locked  = d < today
#                             week_sep   = "border-l-2 border-l-gray-400" if d.weekday() == 0 else ""
#                             bg = ("bg-gray-100" if is_closed
#                                   else "bg-amber-100" if is_ha
#                                   else "bg-blue-50" if d == today else "")
#                             with ui.element("td").classes(
#                                 f"{bd} {week_sep} {bg} p-1 text-center"
#                             ):
#                                 if is_closed:
#                                     ui.label("—").classes("text-[12px] text-gray-400")
#                                 elif is_ha:
#                                     ui.label("—").classes("text-[12px] text-amber-600")
#                                 else:
#                                     checked = (child["id"], d_str) not in absent
#                                     ui.checkbox(
#                                         value=checked,
#                                         on_change=lambda e, cid=child["id"], ds=d_str:
#                                             toggle_absence(cid, ds, absent=not e.value)
#                                     ).props("dense" + (" disable" if is_locked else ""))

#                 # Totals row
#                 with ui.element("tr"):
#                     with ui.element("td").classes(f"{bd} bg-gray-50 px-2 py-1 font-semibold whitespace-nowrap sticky"):
#                         ui.label("Gesamt")
#                     for d in days:
#                         d_str = d.isoformat()
#                         is_closing = d_str in closing_days
#                         week_sep   = "border-l-2 border-l-gray-400" if d.weekday() == 0 else ""
#                         bg = "bg-gray-100" if is_closing else ("bg-blue-50" if d == today else "bg-gray-50")
#                         with ui.element("td").classes(
#                             f"{bd} {week_sep} {bg} text-center py-1.5 px-1"
#                         ):
#                             if is_closing:
#                                 ui.label("—").classes("text-[12px] text-gray-400")
#                             else:
#                                 count = sum(
#                                     1 for c in children
#                                     if (c["id"], d_str) not in absent
#                                     and (c["id"], d_str) not in holiday_absent
#                                 )
#                                 ui.label(str(count)).classes("text-[13px] font-semibold")

#     rebuild()
