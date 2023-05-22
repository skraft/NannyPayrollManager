__author__ = 'Sean Kraft'

from PySide6 import QtWidgets
import sys
import data_provider
import ui

if __name__ == '__main__':
    data = data_provider.DataProvider()

    import reports
    from datetime import date as Date
    employee = data.get_employee_from_name('')
    timesheet = reports.Timesheet(data, employee, start_date=Date(2023, 5, 15), end_date=Date(2023, 5, 19))

    # app = QtWidgets.QApplication([])
    # manager_ui = ui.NannyPayrollMangerUI(data)
    # manager_ui.show()
    # sys.exit(app.exec())
