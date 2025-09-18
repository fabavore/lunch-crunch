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
from tempfile import template

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from order_mailer import OrderMailer
from card_frame import CardFrame, EntryFrame
from order_frame import OrderFrame


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, mailer: OrderMailer, order_frame: OrderFrame):
        super().__init__(parent)

        self.mailer = mailer
        self.order_frame = order_frame

        # Build scrollable frame
        scrolled_frame = ScrolledFrame(self, padding=0, autohide=True)
        scrolled_frame.pack(fill='both', expand=True)

        # canvas = ttk.Canvas(self)
        # scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        # scrollable_frame = ttk.Frame(canvas)
        #
        # scrollable_frame.bind(
        #     '<Configure>',
        #     lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        # )
        #
        # canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        # canvas.configure(yscrollcommand=scrollbar.set)
        #
        # canvas.pack(side='left', fill='both', expand=True)
        # scrollbar.pack(side='right', fill='y')
        #
        # # Mouse wheel scrolling for Linux
        # canvas.bind_all('<Button-4>', lambda e: canvas.yview_scroll(int(-1 * e.num), 'units'))
        # canvas.bind_all('<Button-5>', lambda e: canvas.yview_scroll(int(e.num), 'units'))
        # # Mouse wheel scrolling for Windows
        # canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-1 * e.num), 'units'))

        # Receiver info
        self.receiver_var = ttk.StringVar(value=self.mailer.to_addr)
        self.subject_var = ttk.StringVar(value=self.mailer.subject)
        receiver_fields = [
            ('E-Mail Adresse', self.receiver_var), ('Betreff', self.subject_var)
        ]
        receiver_frame = EntryFrame(
            scrolled_frame, receiver_fields, title='Empfänger', width=40
        )
        receiver_frame.pack(anchor='w')

        # Template edit
        template_card = CardFrame(scrolled_frame, title='Vorlage',
                                  subtitle='E-Mail Vorlage bearbeiten')
        template_card.pack(fill='x', expand=True)

        self.template_text = ttk.Text(template_card.content, height=10)
        self.template_text.pack(fill='x', expand=True)

        self.template_text.insert('1.0', self.mailer.template)

        self.receiver_var.trace('w', lambda var, index, mode: self.update_preview())
        self.subject_var.trace('w', lambda var, index, mode: self.update_preview())
        self.template_text.bind('<KeyRelease>', lambda *args: self.update_preview())

        self.show_advanced = ttk.BooleanVar(value=False)
        advanced_checkbox = ttk.Checkbutton(
            scrolled_frame,
            text='Erweiterte Einstellungen',
            command=self.toggle_advanced,
            variable=self.show_advanced,
            style='Outline.Toolbutton'
        )
        advanced_checkbox.pack(pady=10)

        self.advanced = AdvancedSettingsFrame(scrolled_frame)

        self.save_btn = ttk.Button(scrolled_frame, command=self.save_settings, text='Speichern')

        self.toggle_advanced()

    def toggle_advanced(self):
        if self.show_advanced.get():
            self.save_btn.pack_forget()
            self.advanced.pack()
        else:
            self.advanced.pack_forget()
        self.save_btn.pack(pady=(0, 20))

    def update_preview(self):
        self.mailer.config['receiver']['addr'] = self.receiver_var.get()
        self.mailer.config['receiver']['subject'] = self.subject_var.get()
        template = self.template_text.get('1.0', 'end').strip()
        self.mailer.template = template
        self.order_frame.update_preview()

    def save_settings(self):
        self.mailer.save_config()
        self.mailer.save_template()


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
