__author__ = 'Sean Kraft'

from PySide6 import QtWidgets
import sys
import data_provider
import ui

# TODO add milage calculator


if __name__ == '__main__':
    data = data_provider.DataProvider()

    app = QtWidgets.QApplication([])
    manager_ui = ui.NannyPayrollMangerUI(data)
    manager_ui.show()
    sys.exit(app.exec())
