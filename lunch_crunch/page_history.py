from nicegui import ui, events

from .common import order_manager, header


@ui.page('/history')
def history_page() -> None:
    header()

    def on_month_change(e: events.ValueChangeEventArguments):
        order_manager.selected_month = e.value
        history_page.refresh()

    with ui.card().classes('w-full m-4'):
        ui.item_label('Bestellungshistorie').props('caption').classes('text-lg')

        ui.select(
            options=order_manager.month_options,
            value=order_manager.selected_month,
            on_change=on_month_change,
        )

        rows = [
            {
                'date':   o.datetime.strftime('%d.%m.%Y %H:%M'),
                'counts': ', '.join(f'{k}: {v}' for k, v in o.counts.items()),
                'total':  o.total_count,
            }
            for o in reversed(order_manager.filtered_orders)
        ]
        columns = [
            {'name': 'date',   'label': 'Datum',        'field': 'date'},
            {'name': 'counts', 'label': 'Bestellungen', 'field': 'counts'},
            {'name': 'total',  'label': 'Summe',        'field': 'total'},
        ]
        ui.table(rows=rows, columns=columns, pagination=10).classes('w-full')

        with ui.column(align_items='end').classes('w-full'):
            with ui.row():
                with ui.card(align_items='center').classes('q-pa-sm'):
                    ui.label().bind_text_from(
                        order_manager, 'total_count',
                        lambda total: f'SUMME: {total}'
                    ).classes('text-primary text-weight-bold')

                def history_download():
                    lines = ['Datum;Bestellungen;Summe']
                    for o in order_manager.filtered_orders:
                        counts_str = ', '.join(f'{k}: {v}' for k, v in o.counts.items())
                        lines.append(f'{o.datetime.strftime("%d.%m.%Y %H:%M")};{counts_str};{o.total_count}')
                    return ui.download.content(
                        '\n'.join(lines),
                        filename=f'Bestellungen {order_manager.selected_month}.csv',
                        media_type='text/csv',
                    )

                ui.button('Historie herunterladen', on_click=history_download).props('icon=download')
