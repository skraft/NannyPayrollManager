__author__ = 'Sean Kraft'

import data_provider
import reports
from datetime import date as Date
from pathlib import Path

if __name__ == '__main__':
    data = data_provider.DataProvider()

    # data.add_worked_time(Date(2023, 5, 8), 'John Doe', 8)
    # data.add_worked_time(Date(2023, 5, 9), 'John Doe', 8)
    # data.add_worked_time(Date(2023, 5, 10), 'John Doe', 8.25)
    # # data.add_worked_time(Date(2023, 5, 5), 'John Doe', 8)
    # data.save()

    employee = data.get_employee_from_name('John Doe')
    start_date = Date(2023, 5, 8)
    end_date = Date(2023, 5, 12)
    timesheet = reports.Timesheet(data, employee, start_date=start_date, end_date=end_date)
    timesheet_path = Path.home() / "Downloads" / f"Payroll_{employee.name.replace(' ', '')}_{end_date.isoformat()}.pdf"
    timesheet.to_pdf(timesheet_path)
