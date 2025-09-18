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
from typing import List, Tuple

import ttkbootstrap as ttk


TITLE_FONT = ('Segoe UI', 14, 'bold')
SUBTITLE_FONT = ('Segoe UI', 10)


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
