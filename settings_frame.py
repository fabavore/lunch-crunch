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

        self.advanced = ttk.Frame(scrolled_frame)

        # SMTP info
        self.smtp_server_var = ttk.StringVar(value=self.mailer.smtp_server)
        self.smtp_port_var = ttk.IntVar(value=self.mailer.smtp_port)
        self.from_addr_var = ttk.StringVar(value=self.mailer.from_addr)
        self.password_var = ttk.StringVar(value=self.mailer.password)
        self.use_tls_var = ttk.BooleanVar(value=self.mailer.use_tls)
        smtp_fields = [
            ('SMTP Server', self.smtp_server_var),
            ('SMTP Port', self.smtp_port_var),
            ('E-Mail-Adresse', self.from_addr_var),
            ('E-Mail Password', self.password_var)
        ]
        smtp_frame = EntryFrame(
            self.advanced, smtp_fields, title='SMTP Konfiguration', width=40
        )
        use_tls = ttk.Checkbutton(smtp_frame.content, variable=self.use_tls_var,
                                  text="TLS-Verschlüsselung aktivieren (empfohlen)")
        smtp_frame.content_frames.append(use_tls)
        smtp_frame.place_content_frames()
        smtp_frame.pack(anchor='w')

        # Groups
        self.groups_var = ttk.StringVar(value=', '.join(self.mailer.groups))
        groups_frame = EntryFrame(
            self.advanced, [('Gruppennamen', self.groups_var)],
            title='Verschiedenes', width=40
        )
        groups_frame.pack(anchor='w')

        self.save_btn = ttk.Button(scrolled_frame, command=self.save_settings, text='Speichern')

        self.toggle_advanced()

    def toggle_advanced(self):
        if self.show_advanced.get():
            self.save_btn.pack_forget()
            self.advanced.pack(anchor='w')
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
        self.mailer.config['sender']['server'] = self.smtp_server_var.get()
        self.mailer.config['sender']['port'] = self.smtp_port_var.get()
        self.mailer.config['sender']['addr'] = self.from_addr_var.get()
        self.mailer.config['sender']['password'] = self.password_var.get()
        self.mailer.config['sender']['use_tls'] = self.use_tls_var.get()
        self.mailer.config['groups'] = [g.strip() for g in self.groups_var.get().split(',')]
        self.mailer.save_config()
        self.mailer.save_template()
        self.order_frame.update_groups()
