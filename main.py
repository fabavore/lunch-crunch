#   LunchCrunch: A Python desktop app to manage food ordering
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
from collections import namedtuple
from typing import Dict, Tuple, List

import ttkbootstrap as ttk


DEFAULT_TEMPLATE = """Liebe:r Essenslieferant:in,

für unseren Kindergarten möchten wir heute {anzahl} Portionen Essen bestellen.

Mit besten Grüßen

Kindergarten Tierkinder"""

DEFAULT_GROUPS = ['Hasen:', 'Igel:', 'Rehkids:']

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
                subtitle_label = ttk.Label(title_frame, text=subtitle, font=SUBTITLE_FONT,
                                           bootstyle='secondary')
                subtitle_label.pack(anchor='w', pady=(2, 0))

        self.content = ttk.Frame(self)
        self.content.pack(anchor='w', padx=20, pady=(0, 20))


class EntryFrame(CardFrame):
    def __init__(self, parent, fields: List[Tuple[str, ttk.Variable]],
                 title=None, subtitle=None, *args, **kwargs):
        super().__init__(parent, title, subtitle)

        self.content_frames = []

        for text, var in fields:
            label = ttk.Label(self.content, text=text, font=('Segoe UI', 10, 'bold'))
            entry = ttk.Entry(self.content, textvariable=var, *args, **kwargs)
            self.content_frames.append((label, entry))

        self.pack_content_frames()

    def pack_content_frames(self):
        for label, entry in self.content_frames:
            label.pack(fill='x', pady=(0, 5))
            entry.pack(anchor='w', pady=(0, 15))


class OrderFrame(ttk.Frame):
    def __init__(self, parent, groups):
        super().__init__(parent)

        self.template = DEFAULT_TEMPLATE
        self.orders = [(g, ttk.IntVar()) for g in groups]

        # Register number validation callback
        val_num = self.register(validate_number)

        entries_frame = EntryFrame(self, self.orders, title='Bestellmengen',
                                   subtitle='Details der Bestellung eingeben',
                                   validate='all', validatecommand=(val_num, '%P'), width=4)
        entries_frame.pack(fill='x')

        preview_frame = CardFrame(self, title='Bestellungsvorschau',)
        preview_frame.pack(fill='x')
        # preview_frame.configure(bootstyle='danger')

        self.preview = ttk.Text(preview_frame.content, height=10, state='disabled')
        self.preview.pack(fill='x')

        self.send_btn = ttk.Button(self, command=self.update_preview, text='Bestellung absenden')
        self.send_btn.pack()

        # Bind events for auto-updating the preview
        for _, v in self.orders:
            v.trace_add('write', lambda var, index, mode: self.update_preview())

        self.update_preview()

    def update_preview(self):
        try:
            total = sum([var.get() for _, var in self.orders])

            self.preview.config(state='normal')
            self.preview.delete('1.0', 'end')
            self.preview.insert('1.0', self.template.format(anzahl=total))
            self.preview.config(state='disabled')
        except Exception as e:
            print(f"Preview error: {e}")


class TemplateFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.template = DEFAULT_TEMPLATE

        # Recipient info
        recipient_info = [(l, ttk.StringVar()) for l in ['E-Mail Adresse:', 'Betreff:']]
        recipient_frame = EntryFrame(self, recipient_info,
                                     title='Empfänger', width=40)
        recipient_frame.pack()

        # Template edit
        template_card = CardFrame(self, title='Vorlage',
                                  subtitle='E-Mail Vorlage bearbeiten')
        template_card.pack(fill='x')

        template_text = ttk.Text(template_card.content)
        template_text.pack(fill='x')

        template_text.insert('1.0', DEFAULT_TEMPLATE)


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, settings):
        super().__init__(parent)

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

        # Sender config
        smtp_info = [(l, ttk.StringVar(value=d)) for l, d in [
            ("SMTP Server:", "smtp.gmail.com"),
            ("SMTP Port:", "587"),
            ("E-Mail Adresse:", ""),
            ("Passwort:", "")
        ]]
        smtp_frame = EntryFrame(scrollable_frame, smtp_info, title='SMTP Konfiguration')
        smtp_frame.pack()

    def save_settings(self):
        pass


class LunchOrderApp(ttk.Window):
    def __init__(self):
        super().__init__(title='🍎 Mittagessenbestellung')
        self.geometry('400x600')
        self.resizable = True
        self.minsize(600, 800)

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        order_frame = OrderFrame(notebook, groups=DEFAULT_GROUPS)
        notebook.add(order_frame, text='🍴 Bestellung')

        template_frame = TemplateFrame(notebook)
        notebook.add(template_frame, text='Vorlage')

        settings_frame = SettingsFrame(notebook, None)
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
