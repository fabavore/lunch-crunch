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

"""Absence page - monthly weekday grid with per-child checkboxes."""

import logging
import smtplib
import ssl
import socket
from email.message import EmailMessage
from email.header import Header
from datetime import date

from nicegui import ui

from lunch_crunch.db import get_db
from lunch_crunch.common import (
    weekdays_of_month, header, get_setting,
    needs_setup, save_groups,
    DEFAULT_EMAIL_SUBJECT, DEFAULT_EMAIL_BODY
)
from lunch_crunch.absence import absence_grid

logger = logging.getLogger(__name__)


@ui.page("/")
def absence_page() -> None:
    """Route "/" - monthly weekday attendance grid with per-child absence checkboxes."""
    today = date.today()

    header()

    def toggle_absence(conn, child_id: int, date_str: str, absent: bool) -> None:
        """Store absences: a row means the child is ABSENT on that date."""
        if absent:
            conn.execute(
                "INSERT OR IGNORE INTO absence (child_id, date) VALUES (?, ?)",
                (child_id, date_str),
            )
        else:
            conn.execute(
                "DELETE FROM absence WHERE child_id = ? AND date = ?",
                (child_id, date_str),
            )

    def get_absent(conn, year, month) -> set:
        month_str = f"{year}-{month:02d}"
        return {
            (r["child_id"], r["date"])
            for r in conn.execute(
                "SELECT child_id, date FROM absence WHERE date LIKE ?",
                (f"{month_str}-%",),
            ).fetchall()
        }

    def get_locked(conn, year, month) -> set:
        month_str = f"{year}-{month:02d}"
        return {
            (r["child_id"], r["date"])
            for r in conn.execute(
                "SELECT child_id, date FROM holiday_absence WHERE date LIKE ?",
                (f"{month_str}-%",),
            ).fetchall()
        }

    def _meal_count() -> int:
        today_str = today.isoformat()
        with get_db() as conn:
            return conn.execute(
                """SELECT COUNT(*) FROM children
                   WHERE DATE(created_at) <= ?
                   AND archived_at IS NULL
                   AND id NOT IN (SELECT child_id FROM absence WHERE date = ?)
                   AND id NOT IN (SELECT child_id FROM holiday_absence WHERE date = ?)""",
                (today_str, today_str, today_str),
            ).fetchone()[0]

    def _render_email(total: int) -> tuple[str, str]:
        """Return (subject, body) rendered with today's date and meal count."""
        with get_db() as conn:
            subj_tpl = get_setting(conn, "email_subject", DEFAULT_EMAIL_SUBJECT)
            body_tpl = get_setting(conn, "email_body", DEFAULT_EMAIL_BODY)
        fmt = {"Datum": today.strftime("%d.%m.%Y"), "Anzahl": total}
        return subj_tpl.format(**fmt), body_tpl.format(**fmt)

    def confirm_send_order() -> None:
        total          = _meal_count()
        subject, body  = _render_email(total)
        with ui.dialog() as dialog, ui.card().classes("w-full max-w-lg"):
            ui.label("Bestellung senden").classes("font-semibold text-lg")
            ui.separator()
            with ui.column().classes("gap-1 w-full"):
                ui.label("Betreff").classes(
                    "text-xs text-gray-400 font-semibold uppercase tracking-wide"
                )
                ui.label(subject).classes("text-sm")
            ui.separator()
            with ui.column().classes("gap-1 w-full"):
                ui.label("Nachricht").classes(
                    "text-xs text-gray-400 font-semibold uppercase tracking-wide"
                )
                ui.label(body).classes("text-sm whitespace-pre-wrap")
            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Abbrechen", on_click=dialog.close).props("flat")
                ui.button(
                    "Senden", icon="send",
                    on_click=lambda: (dialog.close(), send_order()),
                ).props("color=positive")
        dialog.open()

    def send_order():
        with get_db() as conn:
            host      = get_setting(conn, "smtp_host")
            port      = get_setting(conn, "smtp_port", "587")
            user      = get_setting(conn, "smtp_user")
            password  = get_setting(conn, "smtp_password")
            recipient = get_setting(conn, "provider_email")

        if not all([host, user, password, recipient]):
            ui.notify(
                "SMTP nicht konfiguriert - bitte zuerst in den Einstellungen eintragen", 
                type="warning"
            )
            return

        total          = _meal_count()
        subject, body  = _render_email(total)

        msg = EmailMessage()
        msg["Subject"] = Header(subject).encode()
        msg["From"]    = Header(user).encode()
        msg["To"]      = recipient

        msg.set_content(body)

        local_hostname = socket.getfqdn().encode('ascii', 'ignore').decode('ascii') or 'localhost'

        try:
            with smtplib.SMTP(host, int(port), local_hostname) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(user, password)
                smtp.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            logger.error("SMTP send failed: %s", e, exc_info=True)
            ui.notify(f"Fehler beim Senden: {e}", type="negative")
            return

        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO order_log (date, count) VALUES (?, ?)",
                (today.isoformat(), total),
            )
        logger.info("Order sent: %d meals", total)
        ui.notify(f"Bestellung gesendet - {total} Essen", type="positive")
        rebuild()

    def build_send_btn() -> None:
        send_btn = ui.button(
            "Bestellung senden", icon="send", on_click=confirm_send_order
        )

        with get_db() as conn:
            today_is_closed = conn.execute(
                "SELECT 1 FROM closing_days WHERE date = ?", (today.isoformat(),)
            ).fetchone() is not None
            order_sent_today = conn.execute(
                "SELECT 1 FROM order_log WHERE date = ?", (today.isoformat(),)
            ).fetchone() is not None
        closed_or_sent = today_is_closed or order_sent_today
        send_btn.set_enabled(not closed_or_sent)
        send_btn.props("color=positive" if not closed_or_sent else "color=grey")

    def rebuild() -> None:
        absence_grid(
            toggle_absence,
            get_days=lambda conn, year, month: weekdays_of_month(year, month),
            get_absent=get_absent,
            get_locked=get_locked,
            extra_btn=build_send_btn
        )

    if needs_setup():
        _show_setup_dialog()

    rebuild()


def _show_setup_dialog() -> None:
    """Open a first-run dialog to configure group names."""
    inputs: list[ui.input] = []

    def add_row(value: str = "") -> None:
        with group_list:
            row_input = ui.input(placeholder="Gruppenname", value=value)
            inputs.append(row_input)

    def save() -> None:
        groups = [i.value.strip() for i in inputs if i.value.strip()]
        if not groups:
            ui.notify("Bitte mindestens eine Gruppe eingeben", type="warning")
            return
        save_groups(groups)
        dialog.close()
        ui.notify("Gruppen gespeichert", type="positive")

    with ui.dialog().props("persistent") as dialog, ui.card().classes("w-full max-w-sm"):
        ui.label("Willkommen bei MahlZahl").classes("text-xl font-semibold").style("font-family: Antropos;")
        ui.label(
            "Bitte die Gruppen des Kindergartens eintragen."
        ).classes("text-sm text-gray-500")
        ui.separator()
        group_list = ui.column().classes("w-full gap-2")
        add_row()
        add_row()
        ui.button("Gruppe hinzufügen", icon="add", on_click=add_row).props("flat dense")
        ui.separator()
        ui.button("Speichern", icon="save", on_click=save).props("color=primary").classes("self-end")

    dialog.open()
