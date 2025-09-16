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
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class LunchOrder:
    def __init__(self, config_file, template_file):
        self.config_file = config_file
        self.config = self.load_config()

        self.smtp_server = self.config['sender']['smtp_server']
        self.smtp_port = self.config['sender'].getint('smtp_port')
        self.from_addr = self.config['sender']['email']
        self.password = self.config['sender']['password']
        self.use_tls = self.config['sender'].getboolean('use_tls')

        self.to_addr = self.config['receiver']['email']
        self.subject = self.config['receiver']['subject']

        with open(template_file, 'r') as f:
            self.template = f.read()

    def load_config(self):
        try:
            if os.path.isfile(self.config_file):
                config = configparser.ConfigParser()
                config.read(self.config_file)
                return config
        except Exception as e:
            print(f"Error loading config file: {e}")

    def send(self, number):
        email_body = self.template.format(anzahl=number)

        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = self.subject

        msg.attach(MIMEText(email_body, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()

                server.login(self.from_addr, self.password)
                server.sendmail(self.from_addr, self.to_addr, msg.as_string())

            print("Mail sent")
        except Exception as e:
            print(f"Failed to send email: {e}")


if __name__ == '__main__':
    order = LunchOrder('./config.ini', 'template.txt')
    order.send(sys.argv[1])
