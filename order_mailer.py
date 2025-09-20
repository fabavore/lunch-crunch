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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

import tomlkit


class OrderMailer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

        self.order: Dict[str, int] = {g: 0 for g in self.config['groups']}

    def load_config(self):
        if os.path.isfile(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = tomlkit.parse(f.read())
                return config
            except Exception as e:
                print(f"Error loading config file: {e}")
        else:
            return self.create_config()

    @staticmethod
    def create_config():
        config = tomlkit.document()
        config.add(tomlkit.comment('This is the config file for the LunchCrunch food ordering system'))
        config.add(tomlkit.nl())
        config['groups'] = []

        sender = tomlkit.table()
        sender['server'] = 'mail.example.com'
        sender['port'] = 587
        sender['username'] = ''
        sender['password'] = ''
        sender['use_tls'] = True

        receiver = tomlkit.table()
        receiver['addr'] = ''
        receiver['subject'] = ''

        template = tomlkit.table()
        template['text'] = """Order template with {number} as placeholder for the number of items."""
        template['placeholder'] = '{number}'

        config['sender'] = sender
        config['receiver'] = receiver
        config['template'] = template

        return config

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                f.write(tomlkit.dumps(self.config))
        except Exception as e:
            print(f"Error saving config file: {e}")

    @property
    def groups(self):
        return self.config['groups']

    @property
    def smtp_server(self):
        return self.config['sender']['server']

    @property
    def smtp_port(self):
        return self.config['sender']['port']

    @property
    def username(self):
        return self.config['sender']['username']

    @property
    def password(self):
        return self.config['sender']['password']

    @property
    def use_tls(self):
        return self.config['sender']['use_tls']

    @property
    def to_addr(self):
        return self.config['receiver']['addr']

    @property
    def subject(self):
        subject = self.config['receiver']['subject']
        placeholder = self.config['template']['placeholder']
        return subject.replace(placeholder, f'{self.order_total}')

    @property
    def body(self):
        template = self.config['template']['text']
        placeholder = self.config['template']['placeholder']
        return template.replace(placeholder, f'{self.order_total}')

    @property
    def order_total(self):
        return sum(self.order.values())

    def send_email(self):
        if not self.smtp_server or not self.smtp_port:
            raise Exception(f"SMTP Server und/oder Port nicht konfiguriert: {self.config_file}")
        if not self.username or not self.password:
            raise Exception(f"Absenderadresse und/oder Passwort nicht konfiguriert: {self.config_file}")
        if not self.to_addr:
            raise Exception(f"Bitte Empfaengeradresse angeben: {self.config_file}")

        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = self.to_addr
        msg['Subject'] = self.subject

        msg.attach(MIMEText(self.body, 'plain'))

        with smtplib.SMTP(self.smtp_server, int(self.smtp_port)) as server:
            if self.use_tls:
                server.starttls()

            server.login(self.username, self.password)
            server.sendmail(self.username, self.to_addr, msg.as_string())
