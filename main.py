__author__ = 'Sean Kraft'

import data_provider
import reports
from datetime import date

if __name__ == '__main__':
    data = data_provider.DataProvider()
    data.add_worked_time(date.today(), 'John Doe', 8)
    data.add_worked_time(date(2023, 4, 30), 'John Doe', 7.5)
    data.add_worked_time(date(2023, 5, 1), 'John Doe', 8.25)
    data.add_worked_time(date(2023, 5, 3), 'John Doe', 7)
    print()
    entries = data.get_worked_time_in_range('John Doe', date(2023, 5, 1), date(2023, 5, 5))
    print(entries)
