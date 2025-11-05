# python
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

from nicegui import ui, events

from order_manager import OrderManager


@ui.refreshable
def history_panel(order_manager: OrderManager):
    with (ui.card().classes('w-full')):
        ui.item_label('Bestellungshistorie').props('caption').classes('text-lg')

        def on_month_change(e: events.ValueChangeEventArguments):
            order_manager.selected_month = e.value
            history_panel.refresh()

        ui.select(
            options=order_manager.month_options,
            value=order_manager.selected_month,
            on_change=on_month_change
        )

        rows = [
            {
                'date': o.datetime.strftime('%d.%m.%Y %H:%M'),
                'counts': ', '.join(f'{k}: {v}' for k, v in o.counts.items()),
                'total': o.total_count
            } for o in reversed(order_manager.filtered_orders)
        ]

        columns = [
            {'name': 'date', 'label': 'Datum', 'field': 'date'},
            {'name': 'counts', 'label': 'Bestellungen', 'field': 'counts'},
            {'name': 'total', 'label': 'Summe', 'field': 'total'},
        ]

        ui.table(rows=rows, columns=columns, pagination=10).classes('w-full')

        with ui.column(align_items='end').classes('w-full'):
            with ui.row():
                with ui.card(align_items='center').classes('q-pa-sm'):
                    ui.label().bind_text_from(
                        order_manager,
                        'total_count',
                        lambda total: f'SUMME: {total}'
                    ).classes('text-primary text-weight-bold')

                def history_download() -> str:
                    lines = ['Datum;Bestellungen;Summe']
                    for o in order_manager.filtered_orders:
                        counts_str = ', '.join(f'{k}: {v}' for k, v in o.counts.items())
                        line = f'{o.datetime.strftime("%d.%m.%Y %H:%M")};{counts_str};{o.total_count}'
                        lines.append(line)
                    return ui.download.content(
                        '\n'.join(lines),
                        filename=f'Bestellungen {order_manager.selected_month}.csv',
                        media_type='text/csv'
                    )

                ui.button('Historie herunterladen', on_click=history_download).props('icon=download')
