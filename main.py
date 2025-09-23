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
import logging
import os
import sys

from nicegui import app, ui, events
from platformdirs import user_config_path, user_log_path

from order_mailer import OrderMailer, OrderMailerConfigError

# Force UTF-8 for PyInstaller executables
if getattr(sys, 'frozen', False):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

NAME = 'Mittagessen'

CONFIG_PATH = user_config_path(appname=NAME, appauthor=False, ensure_exists=True)
CONFIG_FILE = CONFIG_PATH / 'config.toml'

LOG_PATH = user_log_path(appname=NAME, appauthor=False, ensure_exists=True)
LOG_FILE = LOG_PATH / f'{NAME}.log'

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup():
    app.add_static_files('/assets', os.path.join(os.path.dirname(__file__), 'assets'))

    ui.add_head_html('''
    <style>
    @font-face {
        font-family: 'Antropos';
        src: url('/assets/AntroposFreefont-BW2G.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
    }
    body {
        background: url("/assets/Hintergrund_Startseite.png") no-repeat center center fixed;
        background-size: cover;
    }
    </style>
    ''')


def place_order():
    try:
        mailer.place_order()
        logger.info('Order placed successfully')
        ui.notify('Bestellung gesendet!')
    except OrderMailerConfigError:
        ui.notify('Fehler: Ungültige Konfiguration. Bitte Einstellungen überprüfen.', type='negative')
    except Exception as e:
        logger.error(f'Error placing order: {e}', exc_info=e)
        ui.notify(f'Fehler beim Senden der Bestellung: {e}', type='negative')


@ui.refreshable
def order_panel():
    with ui.grid(columns='auto 1fr').classes('w-full'):
        with ui.card():
            with ui.card_section():
                with ui.list().props('dense'):
                    for group in mailer.groups:
                        with ui.item():
                            def on_change(e, group=group):
                                mailer.order[group] = int(e.value) or 0

                            ui.number(group, min=0, precision=0, step=1,
                                      format='%d', on_change=on_change).style('font-family: Antropos;')
            with ui.card_section():
                with ui.column(align_items='center'):
                    with ui.card(align_items='center').classes('q-pa-sm w-full'):
                        ui.label().bind_text_from(mailer, 'order_total', lambda total: f'Summe: {total}')

                    ui.button('Bestellung senden', on_click=place_order, icon='send')
        with ui.card():
            with ui.list().props('separator').classes('w-full'):
                ui.item_label('Bestellungsübersicht').props('caption').classes('text-lg q-mb-md')
                with ui.item():
                    with ui.item_section().props('side'):
                        ui.icon('mail')
                    with ui.item_section():
                        ui.label().bind_text_from(mailer, 'to_addr')
                with ui.item():
                    with ui.item_section().props('side'):
                        ui.icon('subject')
                    with ui.item_section():
                        ui.label().bind_text_from(mailer, 'subject')
                with ui.item():
                    ui.restructured_text().bind_content_from(mailer, 'body')


def split_values(e: events.ValueChangeEventArguments):
    for value in e.value[:]:
        e.value.remove(value)
        e.value.extend(value.split(','))


def reset_settings():
    mailer.__init__(CONFIG_FILE)
    ui.notify('Einstellungen zurückgesetzt!')
    order_panel.refresh()
    settings_panel.refresh()


def save_settings():
    mailer.save_config()
    ui.notify('Einstellungen gespeichert!')


@ui.refreshable
def settings_panel():
    with ui.grid(columns='auto 1fr').classes('w-full'):
        with ui.card():
            with ui.list().classes('w-full'):
                ui.item_label('SMTP-Konfiguration').props('caption').classes('text-lg q-mb-md')
                (ui.input('Server', placeholder='mail.example.com')
                 .bind_value(mailer, 'smtp_server')
                 .classes('w-full'))
                (ui.number('Port', placeholder='587', min=0, precision=0, step=1, format='%d')
                 .bind_value(mailer, 'smtp_port', forward=int)
                 .classes('w-full'))
                (ui.input('Benutzer')
                 .bind_value(mailer, 'username')
                 .classes('w-full'))
                (ui.input('Passwort', password=True, password_toggle_button=True)
                 .bind_value(mailer, 'password')
                 .classes('w-full'))
            ui.switch('TLS-Verschlüsselung (empfohlen)', value=True).bind_value(mailer, 'use_tls')
        with ui.card().classes('w-full'):
            with ui.list().classes('w-full'):
                ui.item_label('Bestellungskonfiguration').props('caption').classes('text-lg q-mb-md')
                (ui.input('Empfänger', placeholder='bestellung@lieferant.de')
                 .bind_value(mailer, 'to_addr')
                 .on_value_change(lambda e: order_panel.refresh())
                 .classes('w-full'))
                (ui.input('Betreff', placeholder='Bestellung')
                 .bind_value(mailer, 'subject_template')
                 .on_value_change(lambda e: order_panel.refresh())
                 .classes('w-full'))
                (ui.textarea('Bestellungsvorlage',
                             placeholder='Bestellungsvorlage mit {Anzahl} als Platzhalter für die Anzahl der Bestellungen.')
                 .bind_value(mailer, 'template')
                 .on_value_change(lambda e: order_panel.refresh())
                 .classes('w-full'))
                (ui.input('Platzhalter', placeholder='{Anzahl}', value='{Anzahl}')
                 .bind_value(mailer, 'placeholder')
                 .on_value_change(lambda e: order_panel.refresh())
                 .classes('w-full'))
    with ui.card().classes('w-full'):
        with ui.column(align_items='end').classes('w-full'):
            (ui.input_chips('Gruppen', new_value_mode='add-unique', on_change=split_values)
             .bind_value(mailer, 'groups')
             .on_value_change(lambda e: order_panel.refresh()).classes('w-full'))
            with ui.row():
                ui.button('Zurücksetzen', on_click=reset_settings, color='standard', icon='refresh')
                ui.button('Einstellungen speichern', on_click=save_settings, icon='save')


def main_panel():
    with ui.tabs().classes('w-full') as tabs:
        one = ui.tab('Bestellung', icon='restaurant').style('font-family: Antropos;')
        two = ui.tab('Einstellungen', icon='settings').style('font-family: Antropos;')
    with ui.tab_panels(tabs, value=one).classes('w-full').style('background: transparent;'):
        with ui.tab_panel(one):
            order_panel()
        with ui.tab_panel(two):
            settings_panel()


if __name__ in {"__main__", "__mp_main__"}:
    logger.info('Application started')
    mailer = OrderMailer(CONFIG_FILE)

    setup()
    main_panel()

    # Add shutdown handling for NiceGUI
    app.on_shutdown(lambda: logger.info('Application shutting down'))

    if sys.platform == 'win32':
        ui.run(title=NAME, native=True, window_size=(800, 600), reload=False)
    else:
        ui.run(title=NAME)