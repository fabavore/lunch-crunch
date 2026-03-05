"""Shared state and header for Lunch Crunch."""

from pathlib import Path

from nicegui import ui
from platformdirs import user_config_path, user_data_path, user_log_path

from .order_manager import OrderManager
from .order_mailer import OrderMailer

NAME = 'Mittagessen'

CONFIG_FILE = user_config_path(appname=NAME, appauthor=False, ensure_exists=True) / 'config.toml'
LOG_FILE    = user_log_path(appname=NAME, appauthor=False, ensure_exists=True) / 'app.log'
DATA_FILE   = user_data_path(appname=NAME, appauthor=False, ensure_exists=True) / 'orders.csv'

order_manager = OrderManager(DATA_FILE)
mailer = OrderMailer(CONFIG_FILE, order_manager)


def header() -> None:
    with ui.header(elevated=True).classes('items-center px-4 gap-2 bg-pink-900/90'):
        ui.label('Mahlzeit').classes('text-white text-xl font-bold').style('font-family: Antropos;')
        ui.space()
        ui.button('Bestellung',    on_click=lambda: ui.navigate.to('/'),
                  icon='restaurant').props('flat color=white').style('font-family: Antropos;')
        ui.button('Historie',      on_click=lambda: ui.navigate.to('/history'),
                  icon='history').props('flat color=white').style('font-family: Antropos;')
        ui.button('Einstellungen', on_click=lambda: ui.navigate.to('/settings'),
                  icon='settings').props('flat color=white').style('font-family: Antropos;')
