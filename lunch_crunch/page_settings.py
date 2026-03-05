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
from datetime import date, datetime, timedelta

from nicegui import ui

from lunch_crunch.db import get_db
from lunch_crunch.common import get_groups, get_setting, save_setting, header


_DE_LOCALE = (
    '{"days":["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"],'
    '"daysShort":["So","Mo","Di","Mi","Do","Fr","Sa"],'
    '"months":["Januar","Februar","März","April","Mai","Juni",'
    '"Juli","August","September","Oktober","November","Dezember"],'
    '"monthsShort":["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],'
    '"firstDayOfWeek":1}'
)
_DATE_PROPS = f"mask='DD.MM.YYYY' :locale='{_DE_LOCALE}'"



@ui.page('/settings')
def settings_page() -> None:
    today = date.today()
    header()

    def reset_settings():
        mailer.__init__(mailer.config_file, mailer.order_manager)
        ui.notify('Einstellungen zurückgesetzt!')
        settings_page.refresh()

    def save_settings():
        mailer.save_config()
        ui.notify('Einstellungen gespeichert!')

    with ui.column().classes('w-full max-w-2xl mx-auto'):
        ui.label("Einstellungen").classes("text-2xl font-semibold").style('font-family: Antropos;')
        ui.separator()

        with ui.tabs().classes("w-full") as tabs:
            tab_children = ui.tab("Kinder", icon="group").style('font-family: Antropos;')
            tab_closing  = ui.tab("Schließtage", icon="block").style('font-family: Antropos;')
            tab_holidays = ui.tab("Schulferien", icon="beach_access").style('font-family: Antropos;')
            tab_smtp     = ui.tab("E-Mail", icon="email").style('font-family: Antropos;')
            tab_log      = ui.tab("Bestellprotokoll", icon="receipt_long").style('font-family: Antropos;')

        def fmt_date(iso: str) -> str:
            return date.fromisoformat(iso).strftime("%d.%m.%Y")

        def parse_date(display: str) -> date:
            return datetime.strptime(display, "%d.%m.%Y").date()

        with ui.tab_panels(tabs, value=tab_children).classes("w-full").style('background: transparent;'):

            # -- Children --
            with ui.tab_panel(tab_children):
                with ui.card().classes("w-full"):
                    def refresh_list() -> None:
                        child_list.clear()
                        with get_db() as conn:
                            rows = conn.execute(
                                "SELECT id, name, group_name FROM children WHERE deleted_at IS NULL ORDER BY name"
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
                                                icon="delete",
                                                on_click=lambda cid=row["id"]: delete_child(cid),
                                            ).props("flat round color=negative size=sm")

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
                        name_input.value   = ""
                        group_select.value = None
                        ui.notify(f"{name} hinzugefügt", type="positive")
                        refresh_list()

                    def delete_child(child_id: int) -> None:
                        with get_db() as conn:
                            conn.execute(
                                "UPDATE children SET deleted_at = datetime('now') WHERE id = ?",
                                (child_id,),
                            )
                        ui.notify("Entfernt", type="info")
                        refresh_list()

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
                                    refresh_list()
                                ui.button("Speichern", on_click=save).props("color=primary")
                        dialog.open()

                    ui.label("Kind hinzufügen").classes("font-medium")
                    with ui.row(align_items="end"):
                        name_input = ui.input("Name")
                        group_select = ui.select(get_groups(), label="Gruppe").classes("w-40")
                        ui.button("Hinzufügen", on_click=add_child, icon="person_add")

                    ui.separator()
                    child_list = ui.column().classes("w-full gap-2")
                    refresh_list()

            # -- Closing days --
            with ui.tab_panel(tab_closing):
                with ui.card().classes("w-full"):
                    ui.label(
                        "Schließtage des Kindergartens - an diesen Tagen keine Bestellungen."
                    ).classes("text-xs text-gray-500")

            # -- Holidays --
            with ui.tab_panel(tab_holidays):
                with ui.card().classes("w-full"):
                    ui.label(
                        "Schulferien - Anwesenheit pro Kind auf der Seite Ferienabfrage konfigurierbar."
                    ).classes("text-xs text-gray-500")

            # -- Email / SMTP --
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

            # -- Order log --
            with ui.tab_panel(tab_log):
                with ui.card().classes("w-full"):
                    ui.label("Noch keine Bestellungen gesendet.").classes("text-gray-500 text-sm")


