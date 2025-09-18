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
import os.path
from datetime import datetime
from typing import Tuple, List

import ttkbootstrap as ttk
from platformdirs import user_config_path
from ttkbootstrap.dialogs import Messagebox

from order_mailer import OrderMailer


TITLE_FONT = ('Segoe UI', 14, 'bold')
SUBTITLE_FONT = ('Segoe UI', 10)


def validate_number(x) -> bool:
    return x.isdigit() or x == ''


class CardFrame(ttk.Frame):
    def __init__(self, parent, title=None, subtitle=None):
        super().__init__(parent)

        if title:
            title_frame = ttk.Frame(self)
            title_frame.pack(fill='x', padx=20, pady=(20, 10))

            title_label = ttk.Label(title_frame, text=title, font=TITLE_FONT)
            title_label.pack(anchor='w')

            if subtitle:
                subtitle_label = ttk.Label(title_frame, text=subtitle,
                                           font=SUBTITLE_FONT, style='secondary')
                subtitle_label.pack(anchor='w', pady=(2, 0))

        self.content = ttk.Frame(self)
        self.content.pack(anchor='w', fill='x', expand=True, padx=20, pady=(0, 20))


class EntryFrame(CardFrame):
    def __init__(self, parent, fields: List[Tuple[str, ttk.Variable]],
                 title=None, subtitle=None, *args, **kwargs):
        super().__init__(parent, title, subtitle)

        self.content_frames = []

        for text, var in fields:
            frame = ttk.Frame(self.content)
            self.content_frames.append(frame)

            label = ttk.Label(frame, text=f'{text}:', font=('Segoe UI', 10, 'bold'))
            label.pack(fill='x', pady=(0, 5))

            entry = ttk.Entry(frame, textvariable=var, *args, **kwargs)
            entry.pack(anchor='w')

        self.place_content_frames()

    def place_content_frames(self):
        for i, frame in enumerate(self.content_frames):
            frame.grid(row=i, column=0, pady=(0, 10))


class OrderEntryFrame(EntryFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def place_content_frames(self):
        for i, frame in enumerate(self.content_frames):
            frame.grid(row=0, column=i, padx=(0, 20))


class OrderFrame(ttk.Frame):
    def __init__(self, parent, mailer: OrderMailer):
        super().__init__(parent)

        self.mailer = mailer
        self.order = [(group, ttk.IntVar()) for group in mailer.groups]

        # Register number validation callback
        val_num = self.register(validate_number)

        entries_frame = OrderEntryFrame(self, self.order, title='Bestellmengen',
                                   subtitle='Details der Bestellung eingeben',
                                   validate='all', validatecommand=(val_num, '%P'), width=5)
        entries_frame.pack(fill='x')

        preview_frame = CardFrame(self, title='Bestellungsvorschau')
        preview_frame.pack(fill='x')

        self.preview = ttk.Text(preview_frame.content, height=10, state='disabled')
        self.preview.pack(fill='x')

        self.send_btn = ttk.Button(self, command=self.send_email, text='Bestellung absenden')
        self.send_btn.pack()

        # Bind events for auto-updating the preview
        for _, v in self.order:
            v.trace_add('write', lambda var, index, mode: self.update_preview())

        self.update_preview()

    def update_preview(self):
        try:
            self.mailer.order = {group: var.get() for group, var in self.order}

            self.preview.config(state='normal')
            self.preview.delete('1.0', 'end')
            self.preview.insert('1.0', self.mailer.body)
            self.preview.config(state='disabled')
        except Exception as e:
            print(f"Preview error: {e}")

    def send_email(self):
        pos = (int(self.winfo_rootx() + 0.5 * self.winfo_width()) - 185,
               int(self.winfo_rooty() + 0.33 * self.winfo_height()))
        try:
            self.mailer.send_email()
            Messagebox.show_info(f'Bestellung abgeschickt um {datetime.now().strftime('%H:%M')} Uhr.', title='Bestätigung', position=pos)
        except Exception as e:
            Messagebox.show_error(f'Bestellung konnte nicht abgeschickt werden: {e}', title='Fehler', position=pos)


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, mailer: OrderMailer):
        super().__init__(parent)

        self.mailer = mailer

        # Build scrollable frame
        canvas = ttk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Mouse wheel scrolling for Linux
        canvas.bind_all('<Button-4>', lambda e: canvas.yview_scroll(int(-1 * e.num), 'units'))
        canvas.bind_all('<Button-5>', lambda e: canvas.yview_scroll(int(e.num), 'units'))
        # Mouse wheel scrolling for Windows
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-1 * e.num), 'units'))

        # Receiver info
        [print(x) for x in mailer.config['receiver']]
        self.receiver_info = [
            ('E-Mail Adresse', ttk.StringVar(value=self.mailer.to_addr)),
            ('Betreff', ttk.StringVar(value=self.mailer.subject)),
        ]
        receiver_frame = EntryFrame(scrollable_frame, self.receiver_info,
                                     title='Empfänger', width=40)
        receiver_frame.pack(anchor='w')

        # Template edit
        template_card = CardFrame(scrollable_frame, title='Vorlage',
                                  subtitle='E-Mail Vorlage bearbeiten')
        template_card.pack(fill='x', expand=True)

        template_text = ttk.Text(template_card.content, height=10)
        template_text.pack(fill='x', expand=True)

        template_text.insert('1.0', self.mailer.template)

        self.show_advanced = ttk.BooleanVar(value=False)
        advanced_checkbox = ttk.Checkbutton(
            scrollable_frame,
            text='Erweiterte Einstellungen',
            command=self.toggle_advanced,
            variable=self.show_advanced,
            style='Outline.Toolbutton'
        )
        advanced_checkbox.pack(pady=10)

        self.advanced = AdvancedSettingsFrame(scrollable_frame)

        self.save_btn = ttk.Button(scrollable_frame, command=self.save_settings, text='Speichern')

        self.toggle_advanced()

    def toggle_advanced(self):
        if self.show_advanced.get():
            self.save_btn.pack_forget()
            self.advanced.pack()
        else:
            self.advanced.pack_forget()
        self.save_btn.pack(pady=(0, 20))

    def save_settings(self):
        receiver_info = [var.get() for _, var in self.receiver_info]
        self.mailer.config['receiver']['email'] = receiver_info[0]
        self.mailer.config['receiver']['subject'] = receiver_info[1]

        self.mailer.save_config()


class AdvancedSettingsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Sender config
        smtp_info = [(l, ttk.StringVar(value=d)) for l, d in [
            ("SMTP Server:", "smtp.gmail.com"),
            ("SMTP Port:", "587"),
            ("E-Mail Adresse:", ""),
            ("Passwort:", "")
        ]]
        smtp_frame = EntryFrame(self, smtp_info, title='SMTP Konfiguration', width=40)
        smtp_frame.pack(fill='x')


class LunchOrderApp(ttk.Window):
    def __init__(self):
        super().__init__(title='🍎 Mittagessenbestellung')
        self.geometry('750x700')
        self.resizable = True
        self.minsize(750, 600)

        config_path = user_config_path(appname='mittagessen')
        config_file = config_path / 'config.toml'

        mailer = OrderMailer(config_file)

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        order_frame = OrderFrame(notebook, mailer=mailer)
        notebook.add(order_frame, text='🍴 Bestellung')

        settings_frame = SettingsFrame(notebook, mailer=mailer)
        notebook.add(settings_frame, text='⚙️ Einstellungen')



    def on_closing(self):
        print("closing...")
        self.destroy()

    def run(self):
        self.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.mainloop()


def main():
    app = LunchOrderApp()
    app.run()


if __name__ == '__main__':
    main()
