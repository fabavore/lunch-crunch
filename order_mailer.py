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
        config = self.load_config()

        self.groups = config.get('groups', [])
        self.order: Dict[str, int] = {group: 0 for group in self.groups}

        self.smtp_server = config.get('sender', {}).get('server', '')
        self.smtp_port = config.get('sender', {}).get('port', 587)
        self.username = config.get('sender', {}).get('username', '')
        self.password = config.get('sender', {}).get('password', '')
        self.use_tls = config.get('sender', {}).get('use_tls', True)

        self.to_addr = config.get('receiver', {}).get('addr', '')
        self.subject_template = config.get('receiver', {}).get('subject', '')

        self.template = config.get('template', {}).get('text', '')
        self.placeholder = config.get('template', {}).get('placeholder', '{number}')

    def load_config(self):
        try:
            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = tomlkit.parse(f.read())
                return config
        except Exception as e:
            print(f"Error loading config file: {e}")

    def create_config(self):
        config = tomlkit.document()
        config.add(tomlkit.comment('This is the config file for the LunchCrunch food ordering system'))
        config.add(tomlkit.nl())
        config['groups'] = self.groups

        sender = tomlkit.table()
        sender['server'] = self.smtp_server
        sender['port'] = self.smtp_port
        sender['username'] = self.username
        sender['password'] = self.password
        sender['use_tls'] = self.use_tls

        receiver = tomlkit.table()
        receiver['addr'] = self.to_addr
        receiver['subject'] = self.subject_template

        template = tomlkit.table()
        template['text'] = self.template
        template['placeholder'] = self.placeholder

        config['sender'] = sender
        config['receiver'] = receiver
        config['template'] = template

        return config

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(tomlkit.dumps(self.create_config()))
        except Exception as e:
            print(f"Error saving config file: {e}")

    @property
    def order_total(self):
        return sum(self.order.values())

    @property
    def subject(self):
        return self.subject_template.replace(self.placeholder, f'{self.order_total}')

    @property
    def body(self):
        return self.template.replace(self.placeholder, f'{self.order_total}')

    def send_order(self):
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
