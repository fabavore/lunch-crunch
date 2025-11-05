# python
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
import ast
import logging
from datetime import datetime
from typing import List

from order import DATE_FORMAT, Order

logger = logging.getLogger(__name__)

"""
Module `order_manager`

Provides the OrderManager class which loads, stores and filters `Order`
objects persisted in a simple text file. Each line in the file is expected
to contain a semicolon-separated record: date;counts;total_count.

The module exposes:
- OrderManager: manages the in-memory list of orders and persistence.
"""


class OrderManager:
    """
    Manage a collection of `Order` objects loaded from a text data file.

    Responsibilities:
    - load orders from `data_file`
    - append new orders to `data_file`
    - provide month selection options and filtered views
    - compute total counts for the current filter

    Parameters
    - data_file: path to the text file used for persistence
    """

    def __init__(self, data_file: str):
        self.data_file = data_file
        self.orders: List[Order] = self.load_orders()

        self.selected_month = 'Alle Monate'

    def load_orders(self) -> List[Order]:
        """
        Read orders from the configured data file.

        Each non-empty line is expected to be of the form:
        date_str;counts_str;other

        - date_str is parsed using `DATE_FORMAT`
        - counts_str is parsed with `ast.literal_eval` into a dict
        - other fields are ignored (kept for backward compatibility)

        Returns:
        - list of parsed `Order` objects
        """
        try:
            orders: List[Order] = []
            with open(self.data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    date_str, counts_str, _ = line.split(';')

                    dt = datetime.strptime(date_str, DATE_FORMAT)
                    counts = ast.literal_eval(counts_str)

                    order = Order(counts=counts, datetime=dt)
                    orders.append(order)
                except Exception as e:
                    # Log parse issues but continue processing remaining lines
                    logger.warning(f'Could not parse order line: {line}. Error: {e}')
            logger.info(f'Loaded {len(orders)} orders from {self.data_file}')
            return orders
        except FileNotFoundError:
            # If the file doesn't exist, create it with a header and return empty list
            logger.info(f'Data file not found: {self.data_file}. Starting with empty order list.')
            with open(self.data_file, 'a', encoding='utf-8') as f:
                f.write('datetime,counts,total_count\n')
            return []
        except Exception as e:
            logger.error(f'Could not load data file: {e}')
            return []

    def add_order(self, order: Order):
        """
        Append an `Order` to the data file and to the in-memory list.

        Parameters:
        - order: Order instance to persist and store.

        Raises:
        - re-raises any I/O exceptions after logging them.
        """
        try:
            with open(self.data_file, 'a', encoding='utf-8') as f:
                f.write(str(order) + '\n')
            self.orders.append(order)
            logger.info(f'Added new order to {self.data_file}: {order}')
        except Exception as e:
            logger.error(f'Could not add order to data file: {e}')
            raise

    @property
    def month_options(self) -> List[str]:
        """
        Build a list of month selection options for the UI selector.

        Format:
        - first entry: 'Alle Monate'
        - subsequent entries: 'month/year' (e.g. '7/2025'), sorted newest first

        Returns:
        - list of option strings
        """
        month_set = {(o.datetime.year, o.datetime.month) for o in self.orders}
        month_list = sorted(month_set, reverse=True)
        # convert (year, month) tuples back into 'month/year' strings
        return ['Alle Monate'] + [f'{m}/{y}' for y, m in month_list]

    @property
    def filtered_orders(self) -> List[Order]:
        """
        Return orders filtered by the currently selected month.

        If `selected_month` is 'Alle Monate' all orders are returned.
        Otherwise `selected_month` is expected in the format 'month/year'.

        Returns:
        - list of Order instances matching the filter
        """
        if self.selected_month != 'Alle Monate':
            month, year = map(int, self.selected_month.split('/'))
            return [o for o in self.orders if o.datetime.year == year and o.datetime.month == month]
        return self.orders

    @property
    def total_count(self) -> int:
        """
        Compute the sum of `total_count` for all currently filtered orders.

        Returns:
        - integer sum of order totals
        """
        return sum(o.total_count for o in self.filtered_orders)
