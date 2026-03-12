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

"""Reusable month-navigation + group-filter widget for grid pages."""

from datetime import date

from nicegui import ui

from lunch_crunch.common import get_groups


def month_and_group_filter(current, update, has_data=None) -> None:
    """Render prev/next month buttons, a month label, a "Heute" button, and a group selector.

    Args:
        current:  Mutable dict with keys ``year``, ``month``, ``group``.
                  Updated in-place when the user navigates or selects a group.
        update:   Called after every state change to refresh the page content.
        has_data: Optional callable ``(year, month) -> bool``.  When provided,
                  the prev/next buttons are disabled for months that return False.
    """
    def _adj(delta: int) -> tuple[int, int]:
        m = current["month"] + delta
        y = current["year"]
        if m > 12:
            return 1, y + 1
        if m < 1:
            return 12, y - 1
        return m, y

    def _refresh_buttons() -> None:
        if has_data is None:
            return
        pm, py = _adj(-1)
        nm, ny = _adj(1)
        prev_btn.set_enabled(has_data(py, pm))
        next_btn.set_enabled(has_data(ny, nm))

    with ui.row(align_items="center").classes("gap-2"):
        def change_month(delta: int) -> None:
            month, year = _adj(delta)
            current["month"], current["year"] = month, year
            month_label.set_text(date(year, month, 1).strftime("%B %Y"))
            update()
            _refresh_buttons()

        def go_today() -> None:
            today = date.today()
            current["year"], current["month"] = today.year, today.month
            month_label.set_text(date(today.year, today.month, 1).strftime("%B %Y"))
            update()
            _refresh_buttons()

        def set_group(value: str) -> None:
            current["group"] = None if value == "Alle Gruppen" else value
            update()

        prev_btn    = ui.button(icon="chevron_left",  on_click=lambda: change_month(-1)).props("flat round")
        month_label = ui.label(
            date(current["year"], current["month"], 1).strftime("%B %Y")
        ).classes("text-xl font-semibold w-44 text-center").style("font-family: Antropos;")
        next_btn    = ui.button(icon="chevron_right", on_click=lambda: change_month(1)).props("flat round")
        ui.button("Heute", on_click=go_today).props("flat dense").style("font-family: Antropos;")
        # ui.separator().props("vertical")
        ui.select(
            options=["Alle Gruppen"] + get_groups(),
            value="Alle Gruppen",
            on_change=lambda e: set_group(e.value),
        ).classes("w-36 mx-4").props("dense outlined")

    _refresh_buttons()
