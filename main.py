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
import logging
import os
import sys
import locale
from pathlib import Path

from nicegui import app, ui

from lunch_crunch.db import init_db
from lunch_crunch.common import LOG_PATH
import lunch_crunch.page_absence            # noqa: F401 — registers route "/"
import lunch_crunch.page_holiday_absence    # noqa: F401 — registers route "/holiday_absence"
import lunch_crunch.page_settings           # noqa: F401 — registers route "/settings"


logging.basicConfig(
    filename=LOG_PATH,
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info('Application started')

try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    pass

init_db()

app.add_static_files('/assets', Path(__file__).parent / 'assets')
ui.add_css("""
    @font-face {
        font-family: 'Antropos';
        src: url('/assets/AntroposFreefont-BW2G.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
    }
    body {
        background-image: url('/assets/Hintergrund_Startseite.png');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
""", shared=True)

if __name__ == '__main__':
    app.on_shutdown(lambda: logger.info('Application shutting down'))
    app.native.window_args['min_size'] = (1360, 768)
    ui.run(
        title='Mahlzeit',
        native=True,
        window_size=(1360, 768),
        reload=False,
    )
