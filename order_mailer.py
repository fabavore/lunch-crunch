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
import smtplib
import socket
from datetime import datetime
from email.message import EmailMessage
from email.header import Header
from typing import Dict

import tomlkit

logger = logging.getLogger(__name__)

class OrderMailerConfigError(Exception):
    pass


class OrderMailer:
    def __init__(self, config_file, data_file):
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
        self.placeholder_number = config.get('template', {}).get('placeholder_number', '{Anzahl}')
        self.placeholder_date = config.get('template', {}).get('placeholder_date', '{Datum}')

        self.data_file = data_file

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = tomlkit.parse(f.read())
            logger.info(f'Config file loaded: {self.config_file}')
            return config
        except FileNotFoundError:
            logger.info(f'Config file not found: {self.config_file}. Using defaults.')
            return {}
        except Exception as e:
            logger.error(f'Could not load config file: {e}')
            return {}

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
        template['placeholder_number'] = self.placeholder_number
        template['placeholder_date'] = self.placeholder_date

        config['sender'] = sender
        config['receiver'] = receiver
        config['template'] = template

        return config

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(tomlkit.dumps(self.create_config()))
            logger.info(f'Config file saved: {self.config_file}')
        except Exception as e:
            logger.error(f'Could not save config file: {e}')

    @property
    def order_total(self):
        return sum(self.order.values())

    @property
    def subject(self):
        return self.fill_placeholders(self.subject_template)

    @property
    def body(self):
        return self.fill_placeholders(self.template)

    def fill_placeholders(self, text: str) -> str:
        return (text
                .replace(self.placeholder_number, f'{self.order_total}')
                .replace(self.placeholder_date, datetime.now().strftime('%d.%m.%Y')))

    def place_order(self):
        if not self.smtp_server:
            raise OrderMailerConfigError('SMTP Server')
        if not self.smtp_port:
            raise OrderMailerConfigError('SMTP Port')
        if not self.username:
            raise OrderMailerConfigError('Absenderadresse')
        if not self.password:
            raise OrderMailerConfigError('Passwort')
        if not self.to_addr:
            raise OrderMailerConfigError('Empfängeradresse')

        msg = EmailMessage()
        msg['From'] = Header(self.username, 'utf-8').encode()
        msg['To'] = Header(self.to_addr, 'utf-8').encode()
        msg['Subject'] = Header(self.subject, 'utf-8').encode()

        msg.set_content(self.body, charset='utf-8')

        # Cast smtp_port from tomlkit.items.Integer to int
        self.smtp_port = int(self.smtp_port)
        # Set local hostname for EHLO/HELO command
        # This avoids issues with FQDN containing non-ASCII characters
        try:
            local_hostname = socket.getfqdn().encode('ascii', 'ignore').decode('ascii')
            if not local_hostname:
                local_hostname = 'localhost'
        except:
            local_hostname = 'localhost'

        logger.info(f'Connecting to SMTP server {self.smtp_server}:{self.smtp_port} '
                    f'as {self.username} from {local_hostname} ...')
        with smtplib.SMTP(self.smtp_server, self.smtp_port, local_hostname=local_hostname) as server:
            if self.use_tls:
                server.starttls()

            server.login(self.username, self.password)
            server.send_message(msg)

        with open(self.data_file, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().strftime('%d.%m.%Y %H:%M')}\t'
                    f'{self.order_total}\t{self.subject}\t'
                    f'{self.body.replace("\n", " | ")}\n')
