from nicegui import ui, events

from .common import mailer, header


def split_values(e: events.ValueChangeEventArguments):
    for value in e.value[:]:
        e.value.remove(value)
        e.value.extend(value.split(','))


@ui.page('/settings')
def settings_page() -> None:
    header()

    def reset_settings():
        mailer.__init__(mailer.config_file, mailer.order_manager)
        ui.notify('Einstellungen zurückgesetzt!')
        settings_page.refresh()

    def save_settings():
        mailer.save_config()
        ui.notify('Einstellungen gespeichert!')

    with ui.column().classes('w-full p-4 gap-4'):
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
                    (ui.input_chips('Empfänger', new_value_mode='add-unique', on_change=split_values)
                     .bind_value(mailer, 'to_addr')
                     .classes('w-full'))
                    (ui.input('Betreff', placeholder='Bestellung {Datum}')
                     .bind_value(mailer, 'subject_template')
                     .classes('w-full'))
                    (ui.textarea('Bestellungsvorlage',
                                 placeholder='Bestellungsvorlage mit {Anzahl} als Platzhalter.')
                     .bind_value(mailer, 'template')
                     .classes('w-full'))
                    ui.item_label(f'Nutzbare Platzhalter: {str(mailer.placeholders)}').props('caption')

        with ui.card().classes('w-full'):
            with ui.column(align_items='end').classes('w-full'):
                (ui.input_chips('Gruppen', new_value_mode='add-unique', on_change=split_values)
                 .bind_value(mailer, 'groups')
                 .classes('w-full'))
                with ui.row():
                    ui.button('Zurücksetzen', on_click=reset_settings, color='standard', icon='refresh')
                    ui.button('Einstellungen speichern', on_click=save_settings, icon='save')
