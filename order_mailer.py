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
from tomlkit.exceptions import NonExistentKey


class OrderMailer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

        self.order: Dict[str, int] = {}

    def load_config(self):
        if os.path.isfile(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
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
        sender['server'] = ''
        sender['port'] = ''
        sender['user'] = ''
        sender['password'] = ''
        sender['use_tls'] = True

        receiver = tomlkit.table()
        receiver['addr'] = ''
        receiver['subject'] = ''

        template = tomlkit.table()
        template['file'] = 'template.txt'
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
        try:
            return self.config['groups']
        except NonExistentKey:
            return []

    @property
    def to_addr(self):
        try:
            return self.config['receiver']['addr']
        except NonExistentKey:
            return '<EMAIL>'

    @property
    def subject(self):
        try:
            subject = self.config['receiver']['subject']
            placeholder = self.config['template']['placeholder']
            subject = subject.replace(placeholder, '{number}')
            return subject.format(number=self.sum_order())
        except NonExistentKey:
            return ''

    @property
    def template(self):
        try:
            return self.config['order']['template']
        except NonExistentKey:
            return ''

    @property
    def body(self):
        try:
            template = self.config['order']['template']
            placeholder = self.config['order']['placeholder']
            template = template.replace(placeholder, '{number}')
        except NonExistentKey:
            template = ''
        return template.format(number=self.sum_order())

    def sum_order(self):
        return sum(self.order.values())

    def send_email(self):
        try:
            smtp_server = self.config['sender']['server']
            smtp_port = self.config['sender']['port']
            from_addr = self.config['sender']['user']
            password = self.config['sender']['password']
        except NonExistentKey:
            raise Exception(f"Absenderkonfiguration nicht gefunden: {self.config_file}")

        try:
            use_tls = self.config['sender']['use_tls']
        except NonExistentKey:
            use_tls = True

        if self.to_addr == '<EMAIL>':
            raise Exception(f"Empfängeradresse nicht gefunden: {self.config_file}")

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
        except Exception as e:
            raise e
