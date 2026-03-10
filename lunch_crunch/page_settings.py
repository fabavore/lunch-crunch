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

"""Settings page - tabbed UI for children, closing days, holidays, e-mail, and order log."""

from datetime import date, datetime, timedelta

from nicegui import ui

from lunch_crunch.db import get_db
from lunch_crunch.common import get_groups, get_setting, save_setting, group_date_rows, header, weekdays_of_month


_DE_LOCALE = (
    '{"days":["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"],'
    '"daysShort":["So","Mo","Di","Mi","Do","Fr","Sa"],'
    '"months":["Januar","Februar","März","April","Mai","Juni",'
    '"Juli","August","September","Oktober","November","Dezember"],'
    '"monthsShort":["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],'
    '"firstDayOfWeek":1}'
)
_DATE_PROPS = f"mask='DD.MM.YYYY' :locale='{_DE_LOCALE}'"


@ui.page("/settings")
def settings_page() -> None:
    """Route "/settings" - tabbed settings: children, closing days, holidays, e-mail, log."""
    today = date.today()
    header()

    with ui.column().classes("w-full max-w-2xl mx-auto"):
        ui.label("Einstellungen").classes("text-2xl font-semibold").style("font-family: Antropos;")
        ui.separator()

        with ui.tabs().classes("w-full") as tabs:
            tab_children = ui.tab("Kinder", icon="group").style("font-family: Antropos;")
            tab_closing  = ui.tab("Schließtage", icon="block").style("font-family: Antropos;")
            tab_holidays = ui.tab("Schulferien", icon="beach_access").style("font-family: Antropos;")
            tab_smtp     = ui.tab("E-Mail", icon="email").style("font-family: Antropos;")
            tab_log      = ui.tab("Bestellprotokoll", icon="receipt_long").style("font-family: Antropos;")

        def fmt_date(iso: date) -> str:
            return iso.strftime("%d.%m.%Y")

        def parse_date(display: str) -> date:
            return datetime.strptime(display, "%d.%m.%Y").date()


        with ui.tab_panels(tabs, value=tab_children).classes("w-full").style("background: transparent;"):

            # -- Children ------------------------------------------------------
            with ui.tab_panel(tab_children):
                with ui.card().classes("w-full"):
                    def refresh_children() -> None:
                        child_list.clear()
                        with get_db() as conn:
                            rows = conn.execute(
                                "SELECT id, name, group_name FROM children WHERE archived_at IS NULL ORDER BY name"
                            ).fetchall()
                        with child_list:
                            if not rows:
                                ui.label("Noch keine Kinder eingetragen.").classes("text-sm text-gray-500")
                            for row in rows:
                                with ui.card().classes("w-full"):
                                    with ui.row(align_items="center").classes("w-full justify-between"):
                                        with ui.column().classes("gap-0"):
                                            ui.label(row["name"]).classes("font-semibold")
                                            ui.label(row["group_name"]).classes("text-sm text-gray-500")
                                        with ui.row().classes("gap-0"):
                                            ui.button(
                                                icon="edit",
                                                on_click=lambda cid=row["id"], n=row["name"], g=row["group_name"]:
                                                    open_edit_dialog(cid, n, g),
                                            ).props("flat round size=sm").tooltip("Gruppe ändern")
                                            ui.button(
                                                icon="archive",
                                                on_click=lambda cid=row["id"]: archive_child(cid),
                                            ).props("flat round size=sm").tooltip("Archivieren")

                    def add_child() -> None:
                        name  = name_input.value.strip()
                        group = group_select.value
                        if not name:
                            ui.notify("Bitte einen Namen eingeben", type="warning")
                            return
                        if not group:
                            ui.notify("Bitte eine Gruppe auswählen", type="warning")
                            return
                        with get_db() as conn:
                            conn.execute(
                                "INSERT INTO children (name, group_name) VALUES (?, ?)", (name, group)
                            )
                            child_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                            past_days = [
                                d for d in weekdays_of_month(today.year, today.month)
                                if d <= today
                            ]
                            conn.executemany(
                                "INSERT OR IGNORE INTO holiday_absence (child_id, date) VALUES (?, ?)",
                                [(child_id, d.isoformat()) for d in past_days],
                            )
                        name_input.value   = ""
                        group_select.value = None
                        ui.notify(f"{name} hinzugefügt", type="positive")
                        refresh_children()

                    def archive_child(child_id: int) -> None:
                        remaining_days = [
                            d for d in weekdays_of_month(today.year, today.month)
                            if d > today
                        ]
                        with get_db() as conn:
                            conn.execute(
                                "UPDATE children SET archived_at = datetime('now') WHERE id = ?",
                                (child_id,),
                            )
                            conn.executemany(
                                "INSERT OR IGNORE INTO holiday_absence (child_id, date) VALUES (?, ?)",
                                [(child_id, d.isoformat()) for d in remaining_days],
                            )
                        ui.notify("Entfernt", type="info")
                        refresh_children()

                    def open_edit_dialog(child_id: int, child_name: str, current_group: str) -> None:
                        with ui.dialog() as dialog, ui.card():
                            ui.label(f"Gruppe ändern für {child_name}").classes("font-medium")
                            new_group_select = ui.select(get_groups(), value=current_group, label="Gruppe").classes("w-full")
                            with ui.row().classes("w-full gap-2"):
                                ui.button("Abbrechen", on_click=dialog.close).props("flat")
                                def save(cid=child_id):
                                    if not new_group_select.value:
                                        ui.notify("Bitte eine Gruppe auswählen", type="warning")
                                        return
                                    with get_db() as conn:
                                        conn.execute(
                                            "UPDATE children SET group_name = ? WHERE id = ?",
                                            (new_group_select.value, cid),
                                        )
                                    dialog.close()
                                    ui.notify("Gruppe aktualisiert", type="positive")
                                    refresh_children()
                                ui.button("Speichern", icon="save", on_click=save).props("color=primary")
                        dialog.open()

                    ui.label("Kind hinzufügen").classes("font-medium")
                    with ui.row(align_items="end").classes("w-full"):
                        name_input = ui.input("Name").classes("flex-1")
                        group_select = ui.select(get_groups(), label="Gruppe").classes("w-40")
                        ui.button("Hinzufügen", icon="person_add", on_click=add_child)

                    ui.separator()
                    child_list = ui.column().classes("w-full gap-2")
                    refresh_children()

            # -- Closing days --------------------------------------------------
            def closing_days(
                tbl:  str = "closing_days",
                desc: str = "Schließtag",
                help_lbl: str = "Schließtage des Kindergartens - an diesen Tagen keine Bestellungen."
            ) -> None:
                """Render the add/delete UI for a date table.

                Reused for both the *Schließtage* and *Schulferien* tabs by passing
                a different ``tbl`` and ``desc``.
                """
                with ui.card().classes("w-full gap-3"):
                    ui.label(help_lbl).classes("text-xs text-gray-500")
                        
                    cd_range_switch = ui.switch("Datumsbereich")

                    with ui.row():
                        with ui.input("Datum", value=fmt_date(today)) as cd_from_input:
                            with ui.menu().props("no-parent-event") as cd_from_menu:
                                with ui.date().props(_DATE_PROPS).bind_value(cd_from_input):
                                    with ui.row().classes("justify-end"):
                                        ui.button("Bestätigen", on_click=cd_from_menu.close).props("flat")
                            with cd_from_input.add_slot("append"):
                                ui.icon("edit_calendar").classes("cursor-pointer").on(
                                    "click", cd_from_menu.open
                                )

                        with ui.input("Bis", value=fmt_date(today)) as cd_to_input:
                            with ui.menu().props("no-parent-event") as cd_to_menu:
                                with ui.date().props(_DATE_PROPS).bind_value(cd_to_input):
                                    with ui.row().classes("justify-end"):
                                        ui.button("Bestätigen", on_click=cd_to_menu.close).props("flat")
                            with cd_to_input.add_slot("append"):
                                ui.icon("edit_calendar").classes("cursor-pointer").on(
                                    "click", cd_to_menu.open
                                )
                        cd_to_input.bind_visibility_from(cd_range_switch, "value")

                    with ui.row(align_items="end").classes("w-full"):
                        cd_note_input = ui.input("Beschreibung (optional)", placeholder="z.B. Sommer").classes("flex-1")

                        def add_closing_days() -> None:
                            from_str = cd_from_input.value
                            if not from_str:
                                ui.notify("Bitte zuerst ein Datum auswählen", type="warning")
                                return
                            if cd_range_switch.value:
                                to_str = cd_to_input.value
                                if not to_str:
                                    ui.notify("Bitte ein Enddatum auswählen", type="warning")
                                    return
                                try:
                                    from_date = parse_date(from_str)
                                    to_date   = parse_date(to_str)
                                except ValueError:
                                    ui.notify("Ungültiges Datum", type="warning")
                                    return
                                if to_date < from_date:
                                    ui.notify("Enddatum muss gleich oder nach Startdatum sein", type="warning")
                                    return
                            else:
                                try:
                                    from_date = to_date = parse_date(from_str)
                                except ValueError:
                                    ui.notify("Ungültiges Datum", type="warning")
                                    return
                            note = cd_note_input.value.strip()
                            added = 0
                            with get_db() as conn:
                                cur = from_date
                                while cur <= to_date:
                                    if cur.weekday() < 5:
                                        conn.execute(
                                            f"INSERT OR IGNORE INTO {tbl} (date, note) VALUES (?, ?)",
                                            (cur, note),
                                        )
                                        added += 1
                                    cur += timedelta(days=1)
                            cd_note_input.value = ""
                            label = from_str if from_date == to_date else f"{from_str} bis {to_str}"
                            ui.notify(f"{added} {desc}{'e' if added > 1 else ''} hinzugefügt: {label}", type="positive")
                            refresh_closing_days()

                        ui.button("Hinzufügen", icon="add", on_click=add_closing_days)

                    ui.separator()
                    closing_day_list = ui.column().classes("w-full gap-2")

                    def delete_closing_days(dates: list) -> None:
                        with get_db() as conn:
                            conn.executemany(f"DELETE FROM {tbl} WHERE date = ?", [(d,) for d in dates])
                        ui.notify(f"{len(dates)} {desc}{'e' if len(dates) > 1 else ''} entfernt", type="info")
                        refresh_closing_days()

                    def refresh_closing_days() -> None:
                        closing_day_list.clear()
                        with get_db() as conn:
                            rows = conn.execute(
                                f"SELECT date, note FROM {tbl} WHERE date >= ? ORDER BY date ASC",
                                (today,),
                            ).fetchall()
                        groups = group_date_rows(rows)
                        with closing_day_list:
                            if not groups:
                                ui.label(f"Keine zukünftigen {desc}e eingetragen.").classes("text-gray-500 text-sm")
                            for frm, to, note, dates in groups:
                                lbl = fmt_date(frm) if frm == to else f"{fmt_date(frm)} bis {fmt_date(to)}"
                                with ui.card().classes("w-full"):
                                    with ui.row(align_items="center").classes("w-full justify-between"):
                                        with ui.column().classes("gap-0"):
                                            ui.label(lbl).classes("font-semibold")
                                            if note:
                                                ui.label(note).classes("text-sm text-gray-500")
                                        with ui.row().classes("gap-0"):
                                            ui.button(
                                                icon="delete",
                                                on_click=lambda ds=dates: delete_closing_days(ds),
                                            ).props("flat round color=negative size=sm").tooltip("Löschen")

                    refresh_closing_days()

            with ui.tab_panel(tab_closing):
                closing_days()

            # -- Holidays ------------------------------------------------------
            with ui.tab_panel(tab_holidays):
                closing_days(
                    "holidays", "Ferientag", 
                    "Schulferien - Anwesenheit pro Kind auf der Seite Ferienabfrage konfigurierbar."
                )

            # -- Email / SMTP --------------------------------------------------
            with ui.tab_panel(tab_smtp):
                with ui.card().classes("w-full gap-2"):
                    ui.label("SMTP-Server").classes("font-medium")
                    host_input      = ui.input("SMTP-Host", value=get_setting("smtp_host")).classes("w-full")
                    port_input      = ui.input("SMTP-Port", value=get_setting("smtp_port", "587")).classes("w-full")
                    user_input      = ui.input("Benutzername (E-Mail Absender)", value=get_setting("smtp_user")).classes("w-full")
                    password_input  = ui.input("Passwort", value=get_setting("smtp_password"), password=True, password_toggle_button=True).classes("w-full")
                    recipient_input = ui.input("Empfänger (E-Mail Essensanbieter)", value=get_setting("provider_email")).classes("w-full")

                with ui.card().classes("w-full gap-2"):
                    ui.label("E-Mail-Inhalt").classes("font-medium")
                    ui.label("Platzhalter: {Datum}  {Anzahl}").classes("text-xs text-gray-500")

                    subject_input = ui.input(
                        "Betreff",
                        value=get_setting("email_subject", "Mittagessen-Bestellung {Datum}"),
                    ).classes("w-full")
                    body_input = ui.textarea(
                        "Text",
                        value=get_setting("email_body",
                                        "Guten Morgen,\n\ndie heutige Mittagessen-Bestellung: {Anzahl} Essen.\n\nMit freundlichen Grüßen,\nLunch Crunch"),
                    ).classes("w-full").props("rows=6")

                    def save_smtp() -> None:
                        save_setting("smtp_host",       host_input.value.strip())
                        save_setting("smtp_port",       port_input.value.strip() or "587")
                        save_setting("smtp_user",       user_input.value.strip())
                        save_setting("smtp_password",   password_input.value)
                        save_setting("provider_email",  recipient_input.value.strip())
                        save_setting("email_subject",   subject_input.value.strip() or "Mittagessen-Bestellung {date}")
                        save_setting("email_body",      body_input.value or "Heutige Mittagessen-Bestellung: {Anzahl} Essen.")
                        ui.notify("Einstellungen gespeichert", type="positive")

                    ui.button("Speichern", icon="save", on_click=save_smtp).classes("self-end")

            # -- Order log -----------------------------------------------------
            with ui.tab_panel(tab_log):
                with ui.card().classes("w-full"):
                    ui.label("Noch keine Bestellungen gesendet.").classes("text-gray-500 text-sm")


