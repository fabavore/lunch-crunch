import logging

from nicegui import ui

from .common import mailer, order_manager, header
from .order_mailer import OrderMailerConfigError, DuplicateOrderError

logger = logging.getLogger(__name__)


@ui.page('/')
def order_page() -> None:
    header()

    def place_order():
        try:
            mailer.place_order()
            order_page.refresh()
            logger.info('Order placed successfully')
            ui.notify('Bestellung gesendet!')
        except OrderMailerConfigError:
            ui.notify('Fehler: Ungültige Konfiguration. Bitte Einstellungen überprüfen.', type='negative')
        except DuplicateOrderError:
            ui.notify('Es wurde bereits eine Bestellung für heute gesendet.', type='warning')
        except Exception as e:
            logger.error(f'Error placing order: {e}', exc_info=e)
            ui.notify(f'Fehler beim Senden der Bestellung: {e}', type='negative')

    with ui.grid(columns='auto 1fr').classes('w-full p-4'):
        with ui.card():
            with ui.card_section():
                with ui.list().props('dense'):
                    for group in mailer.groups:
                        with ui.item():
                            def on_change(e, group=group):
                                mailer.new_order.counts[group] = int(e.value) or 0

                            ui.number(group, min=0, precision=0, step=1,
                                      format='%d', on_change=on_change).style('font-family: Antropos;')
            with ui.card_section():
                with ui.column(align_items='center'):
                    with ui.card(align_items='center').classes('q-pa-sm w-full'):
                        ui.label().bind_text_from(mailer.new_order, 'total_count',
                                                  lambda total: f'SUMME: {total}').classes('text-primary text-weight-bold')
                    ui.button('Bestellung senden', on_click=place_order, icon='send')

        with ui.card():
            with ui.list().props('separator').classes('w-full'):
                ui.item_label('Bestellungsvorschau').props('caption').classes('text-lg q-mb-md')
                with ui.item():
                    with ui.item_section().props('side'):
                        ui.icon('mail')
                    with ui.item_section():
                        ui.label().bind_text_from(mailer, 'to_addr', lambda addr: ', '.join(addr) or '-/-')
                with ui.item():
                    with ui.item_section().props('side'):
                        ui.icon('subject')
                    with ui.item_section():
                        ui.label().bind_text_from(mailer, 'subject')
                with ui.item():
                    with ui.item_section():
                        ui.restructured_text().bind_content_from(mailer, 'body')
