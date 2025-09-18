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
import os

import ttkbootstrap as ttk
from platformdirs import user_config_path

from order_mailer import OrderMailer
from order_frame import OrderFrame
from settings_frame import SettingsFrame


class LunchOrderApp(ttk.Window):
    def __init__(self):
        super().__init__(title='🍎 Mittagessenbestellung')
        self.geometry('750x650')
        self.resizable = True
        self.minsize(750, 650)

        config_path = user_config_path(appname='mittagessen')
        os.makedirs(config_path, exist_ok=True)
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
