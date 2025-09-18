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
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from order_mailer import OrderMailer
from card_frame import CardFrame, EntryFrame


def validate_number(x) -> bool:
    return x.isdigit() or x == ''


class OrderEntryFrame(EntryFrame):
    def place_content_frames(self):
        for i, frame in enumerate(self.content_frames):
            frame.grid(row=0, column=i, padx=(0, 20))


class PreviewFrame(CardFrame):
    def __init__(self, parent, title=None, subtitle=None):
        super().__init__(parent, title, subtitle)

        header = ttk.Frame(self.content)
        header.pack(fill='x')

        receiver_label = ttk.Label(header, text='Empfänger:')
        receiver_label.grid(row=0, column=0, sticky='w', padx=(0, 10), pady=(0, 10))

        self.receiver = ttk.Text(header, height=1, width=40, state='disabled')
        self.receiver.grid(row=0, column=1, sticky='w', pady=(0, 10))

        subject_label = ttk.Label(header, text='Betreff:')
        subject_label.grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(0, 10))

        self.subject = ttk.Text(header, height=1, width=40, state='disabled')
        self.subject.grid(row=1, column=1, sticky='w', pady=(0, 10))

        self.body = ttk.Text(self.content, height=10, state='disabled')
        self.body.pack(fill='x')

    def update(self, receiver=None, subject=None, body=None):
        if receiver:
            self.receiver.config(state='normal')
            self.receiver.delete('1.0', 'end')
            self.receiver.insert('1.0', receiver)
            self.receiver.config(state='disabled')
        if subject:
            self.subject.config(state='normal')
            self.subject.delete('1.0', 'end')
            self.subject.insert('1.0', subject)
            self.subject.config(state='disabled')
        if body:
            self.body.config(state='normal')
            self.body.delete('1.0', 'end')
            self.body.insert('1.0', body)
            self.body.config(state='disabled')


class OrderFrame(ttk.Frame):
    def __init__(self, parent, mailer: OrderMailer):
        super().__init__(parent)

        self.mailer = mailer
        self.order = [(group, ttk.IntVar()) for group in self.mailer.groups]

        # Register number validation callback
        self.val_num = self.register(validate_number)

        self.order_frame = OrderEntryFrame(
            self, self.order,
            title='Bestellmengen', subtitle='Details der Bestellung eingeben',
            validate='all', validatecommand=(self.val_num, '%P'), width=5
        )
        self.order_frame.pack(fill='x')

        self.preview = PreviewFrame(self, title='Bestellungsübersicht')
        self.preview.pack(fill='x')

        self.send_btn = ttk.Button(self, command=self.send_email, text='Bestellung absenden')
        self.send_btn.pack()

        # Bind events for auto-updating the preview
        for _, v in self.order:
            v.trace_add('write', lambda var, index, mode: self.update_preview())

        self.update_preview()

    def update_groups(self):
        self.order = [(group, ttk.IntVar()) for group in self.mailer.groups]

        # Bind events for auto-updating the preview
        for _, v in self.order:
            v.trace_add('write', lambda var, index, mode: self.update_preview())

        self.order_frame.pack_forget()
        self.preview.pack_forget()
        self.send_btn.pack_forget()

        self.order_frame = OrderEntryFrame(
            self, self.order,
            title='Bestellmengen', subtitle='Details der Bestellung eingeben',
            validate='all', validatecommand=(self.val_num, '%P'), width=5
        )
        self.order_frame.pack(fill='x')
        self.preview.pack(fill='x')
        self.send_btn.pack()

    def update_preview(self):
        try:
            self.mailer.order = {group: var.get() for group, var in self.order}
            self.preview.update(
                receiver=self.mailer.to_addr,
                subject=self.mailer.subject,
                body=self.mailer.body
            )
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