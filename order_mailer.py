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
import os
import smtplib
import sys
import textwrap
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

import tomlkit
from tomlkit.exceptions import NonExistentKey

DEFAULT_TEMPLATE = """Liebe:r Essenslieferant:in,

für unseren Kindergarten möchten wir heute {number} Portionen Essen bestellen.

Mit besten Grüßen

Kindergarten"""


class OrderMailer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()
        self.order: Dict[str, int] = {}

    def load_config(self):
        try:
            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = tomlkit.parse(f.read())
                return config
        except Exception as e:
            print(f"Error loading config file: {e}")

    @property
    def groups(self):
        try:
            return self.config['order']['groups']
        except NonExistentKey:
            return []

    @property
    def to_addr(self):
        try:
            return self.config['receiver']['email']
        except NonExistentKey:
            return '<EMAIL>'

    @property
    def subject(self):
        try:
            return self.config['receiver']['subject']
        except NonExistentKey:
            return ''

    @property
    def body(self):
        try:
            template = self.config['order']['template']
            placeholder = self.config['order']['placeholder']
            template = template.replace(placeholder, '{number}')
        except NonExistentKey:
            template = DEFAULT_TEMPLATE
        return template.format(number=self.sum_order())

    def sum_order(self):
        return sum(self.order.values())

    def send_email(self):
        try:
            smtp_server = self.config['sender']['smtp_server']
            smtp_port = self.config['sender']['smtp_port']
            from_addr = self.config['sender']['email']
            password = self.config['sender']['password']
        except NonExistentKey:
            print(f"Absenderkonfiguration nicht gefunden: {self.config_file}")
            return

        try:
            use_tls = self.config['sender']['use_tls']
        except NonExistentKey:
            use_tls = True

        if self.to_addr == '<EMAIL>':
            print(f"Empfängeradresse nicht gefunden: {self.config_file}")
            return

        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = self.subject

        msg.attach(MIMEText(self.body, 'plain'))

        try:
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                if use_tls:
                    server.starttls()

                server.login(from_addr, password)
                server.sendmail(from_addr, self.to_addr, msg.as_string())

            print(f"Bestellung abgeschickt um {datetime.now().strftime('%H:%M')} Uhr.")
        except Exception as e:
            print(f"Bestellung konnte nicht abgeschickt werden: {e}")


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
            mailer.send_email()
            break


if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) > 1 else './config.toml'
    main(config_file)
