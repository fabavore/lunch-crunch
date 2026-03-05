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
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

DATE_FORMAT = '%d.%m.%Y %H:%M'

@dataclass
class Order:
    """
    Represents a single food order with counts per group and a timestamp.

    Attributes:
        counts (Dict[str, int]): Mapping from group/item label to quantity ordered.
        datetime (datetime): Timestamp when the order was created or set.
            Defaults to the time of instantiation if not provided.

    Notes:
        - The `total_count` property computes the total number of items across
          all groups.
    """
    counts: Dict[str, int]
    datetime: datetime = datetime.now()

    @property
    def total_count(self) -> int:
        """
        int: Total number of items in the order, computed as the sum of all
        values in `counts`.
        """
        return sum(self.counts.values())

    def now(self):
        """
        Update the order's timestamp to the current date and time.

        Use when the order is being placed to record the placement time.
        """
        self.datetime = datetime.now()

    def __str__(self):
        """
        Return a compact, human-readable string representation used for CSV storage.

        Format: 'DD.MM.YYYY HH:MM;{counts};{total}'
        """
        return f'{self.datetime.strftime(DATE_FORMAT)};{self.counts};{self.total_count}'
