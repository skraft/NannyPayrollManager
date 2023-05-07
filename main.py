__author__ = 'Sean Kraft'

import data_provider
import reports
from datetime import date as Date

if __name__ == '__main__':
    data = data_provider.DataProvider()
    report = reports.Reports(data)

    # data.add_worked_time(Date(2023, 5, 1), 'John Doe', 8)
    # data.add_worked_time(Date(2023, 5, 2), 'John Doe', 7.75)
    # data.add_worked_time(Date(2023, 5, 3), 'John Doe', 8)
    # data.add_worked_time(Date(2023, 5, 5), 'John Doe', 8)

    # data.save()

    report.timesheet('John Doe', start_date=Date(2023, 5, 1), end_date=Date(2023, 5, 6))
