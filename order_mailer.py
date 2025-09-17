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
import configparser
import os
import smtplib
import textwrap
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


DEFAULT_TEMPLATE = """Liebe:r Essenslieferant:in,

für unseren Kindergarten möchten wir heute {number} Portionen Essen bestellen.

Mit besten Grüßen

Kindergarten"""


class OrderMailer:
    def __init__(self, config_file):
        self.smtp_server = None
        self.smtp_port = None
        self.from_addr = None
        self.password = None
        self.use_tls = None
        self.to_addr = None
        self.subject = None
        self.template = None
        self.order = None

        self.config_file = config_file
        self.config = self.load_config()
        self.load_settings()

    def load_config(self):
        try:
            if os.path.isfile(self.config_file):
                config = configparser.ConfigParser()
                config.read(self.config_file)
                return config
        except Exception as e:
            print(f"Error loading config file: {e}")
            
    def load_settings(self):
        if self.config:
            # Sender configuration
            self.smtp_server = self.config.get('sender', 'smtp_server', fallback=None)
            self.smtp_port = self.config.getint('sender', 'smtp_port', fallback=587)
            self.from_addr = self.config.get('sender', 'email', fallback=None)
            self.password = self.config.get('sender', 'password', fallback=None)
            self.use_tls = self.config.getboolean('sender', 'use_tls', fallback=True)

            # Receiver configuration
            self.to_addr = self.config.get('receiver', 'email', fallback=None)
            self.subject = self.config.get('receiver', 'subject', fallback=None)

            # Template configuration
            template_file = self.config.get('template', 'template_file', fallback=None)
            if template_file and os.path.isfile(template_file):
                with open(template_file, 'r') as f:
                    template = f.read()
                self.template = template.replace(
                    self.config.get('template', 'placeholder'),
                    '{number}'
                )
            else:
                self.template = DEFAULT_TEMPLATE

            # Order configuration
            groups = self.config.get('groups', 'groups',
                                     fallback='Gruppe 1, Gruppe 2, Gruppe 3')
            self.order = {g.strip(): 0 for g in groups.split(',')}

    def sum_order(self):
        return sum(self.order.values())

    def email_body(self):
        return self.template.format(number=self.sum_order())

    def send_email(self):
        if not self.smtp_server or not self.smtp_port:
            print("SMTP-Server nicht konfiguriert.")
            return
        if not self.from_addr or not self.password:
            print("Absenderadresse und/oder Passwort nicht konfiguriert.")
            return
        if not self.to_addr:
            print("Empfängeradresse nicht konfiguriert.")
            return

        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = self.subject

        msg.attach(MIMEText(self.email_body(), 'plain'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.from_addr, self.password)
                server.sendmail(self.from_addr, self.to_addr, msg.as_string())

            print(f"Bestellung abgeschickt um {datetime.now().strftime('%H:%M')} Uhr.")
        except Exception as e:
            print(f"Bestellung konnte nicht abgeschickt werden: {e}")


def place_order(mailer):
    while True:
        print("Bitte Anzahl der benötigten Essen eingeben:")
        order = {}
        for g in mailer.order:
            while True:
                try:
                    order[g] = int(input(f'{g}: '))
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
          f"+{'-' * 78}+\n"
          f"| Empfänger: {mailer.to_addr if mailer.to_addr else '': <66}|\n"
          f"+{'-' * 78}+\n"
          f"| Betreff:   {mailer.subject if mailer.subject else '': <66}|\n"
          f"+{'-' * 78}+\n|{' ' * 78}|")
    for line in mailer.email_body().splitlines():
        for part in textwrap.fill(line, 76).split('\n'):
            print(f"| {part: <76} |")
    print(f"|{' ' * 78}|\n+{'-' * 78}+")


def main():
    print("Wilkommen zur automatischen Mittagessen-Bestellung!\n"
          "===================================================\n")

    mailer = OrderMailer('./config.ini')

    while True:
        place_order(mailer)
        print_preview(mailer)
        choice = input("Bestellung abschicken? [J/n] \n").lower()
        if choice in ['', 'j', 'ja']:
            mailer.send_email()
            break


if __name__ == '__main__':
    main()
