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
import sys
import textwrap
from datetime import datetime

from order_mailer import OrderMailer


def place_order(mailer):
    while True:
        print("Bitte Anzahl der benötigten Essen eingeben:")
        order = {}
        for group in mailer.groups:
            while True:
                try:
                    order[group] = int(input(f'{group}: '))
                    break
                except ValueError:
                    print("Ungültige Eingabe. Bitte eine ganze Zahl eingeben.")
        mailer.order = order
        print(f"Gesamtanzahl: {mailer.sum_order()}")
        choice = input("Alle Eingaben richtig? [J/n] \n").lower()
        if choice in ['', 'j', 'ja']:
            return


def print_preview(mailer):
    print(f"Vorschau Bestellung:\n"
          f"  +{'-' * 78}+\n"
          f"  | Empfänger: {mailer.to_addr: <66}|\n"
          f"  +{'-' * 78}+\n"
          f"  | Betreff: {mailer.subject: <68}|\n"
          f"  +{'-' * 78}+\n  |{' ' * 78}|")
    for line in mailer.body.splitlines():
        for part in textwrap.fill(line, 76).split('\n'):
            print(f"  | {part: <76} |")
    print(f"  |{' ' * 78}|\n  +{'-' * 78}+")


def main(config_file):
    print("Wilkommen zur automatischen Mittagessen-Bestellung!\n"
          "===================================================\n")

    mailer = OrderMailer(config_file)

    while True:
        place_order(mailer)
        print_preview(mailer)
        choice = input("Bestellung abschicken? [J/n] \n").lower()
        if choice in ['', 'j', 'ja']:
            try:
                mailer.send_email()
                print(f"Bestellung abgeschickt um {datetime.now().strftime('%H:%M')} Uhr.")
            except Exception as e:
                print(f"Bestellung konnte nicht abgeschickt werden: {e}")
            break


if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) > 1 else './config.toml'
    main(config_file)
