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
import os

from nicegui import ui
from platformdirs import user_config_path

from order_mailer import OrderMailer


NAME = 'LunchCrunch'


config_path = user_config_path(appname=NAME)
os.makedirs(config_path, exist_ok=True)
config_file = config_path / 'config.toml'

mailer = OrderMailer(config_file)

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
                            ui.number(
                                group, min=0, precision=0, step=1,
                                format='%d', on_change=on_change
                            )
            with ui.card_section():
                with ui.row(align_items='center'):
                    with ui.card().classes('q-pa-sm'):
                        ui.label().bind_text_from(mailer, 'order_total', lambda total: f'Total: {total}')
                    def place_order():
                        try:
                            mailer.send_order()
                            ui.notify('Order placed!')
                        except Exception as e:
                            ui.notify(f'Error: {e}', color='negative')
                    ui.button('Place Order', on_click=place_order)
        with ui.card():
            with ui.list().props('separator').classes('w-full'):
                ui.item_label('Order Summary').props('caption').classes('text-lg q-mb-md')
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

def settings_panel():
    with ui.grid(columns='auto 1fr').classes('w-full'):
        with ui.card():
            with ui.list().classes('w-full'):
                ui.item_label('SMTP Configuration').props('caption').classes('text-lg q-mb-md')
                ui.input('Server', placeholder='mail.example.com') \
                    .bind_value(mailer, 'smtp_server') \
                    .classes('w-full')
                ui.number('Port', placeholder='587', min=0, precision=0, step=1, format='%d') \
                    .bind_value(mailer, 'smtp_port') \
                    .classes('w-full')
                ui.input('User Name') \
                    .bind_value(mailer, 'username') \
                    .classes('w-full')
                ui.input('Password', password=True, password_toggle_button=True) \
                    .bind_value(mailer, 'password') \
                    .classes('w-full')
            ui.switch('TLS Encryption (recommended)', value=True) \
                    .bind_value(mailer, 'use_tls')
        with ui.card().classes('w-full'):
            with ui.list().classes('w-full'):
                ui.item_label('Order Configuration').props('caption').classes('text-lg q-mb-md')
                ui.input('Receiver Address', placeholder='mail@example.com') \
                    .bind_value(mailer, 'to_addr') \
                    .on_value_change(lambda e: order_panel.refresh()) \
                    .classes('w-full')
                ui.input('Subject', placeholder='Order Subject') \
                    .bind_value(mailer, 'subject') \
                    .on_value_change(lambda e: order_panel.refresh()) \
                    .classes('w-full')
                ui.textarea('Order Template', placeholder='Order template with {number} as placeholder for the number of items.') \
                    .bind_value(mailer, 'template') \
                    .on_value_change(lambda e: order_panel.refresh()) \
                    .classes('w-full')
                ui.input('Placeholder', placeholder='{number}', value='{number}') \
                    .bind_value(mailer, 'placeholder') \
                    .on_value_change(lambda e: order_panel.refresh()) \
                    .classes('w-full')
    with ui.card().classes('w-full'):
        with ui.column(align_items='center').classes('w-full'):
            (ui.input_chips('Groups', new_value_mode='add-unique')
                .bind_value(mailer, 'groups')
                .on_value_change(lambda e: order_panel.refresh()).classes('w-full'))
            with ui.row():
                def reset_settings():
                    mailer.__init__(config_file)
                    order_panel.refresh()
                    settings_panel.refresh()
                    ui.notify('Settings reset!')
                def save_settings():
                    mailer.save_config()
                    ui.notify('Settings saved!')
                    # TEST
                    with open(config_file, 'r', encoding='utf-8') as f:
                        print(f.read())
                ui.button('Reset Settings', on_click=reset_settings)
                ui.button('Save Settings', on_click=save_settings)

with ui.tabs().classes('w-full') as tabs:
    one = ui.tab('Order')
    two = ui.tab('Settings')
with ui.tab_panels(tabs, value=one).classes('w-full'):
    with ui.tab_panel(one):
        order_panel()
    with ui.tab_panel(two):
        settings_panel()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title=NAME)
