"""The GUI layer."""

__author__ = 'Sean Kraft'


from PySide6 import QtWidgets, QtCore, QtGui
import data_provider
import reports
from pathlib import Path
import config


class NannyPayrollMangerUI(QtWidgets.QMainWindow):
    UI_NAME = "Nanny Payroll Manager"

    def __init__(self, data_provider: data_provider.DataProvider):
        super().__init__()

        self.data = data_provider
        self.today = QtCore.QDate.currentDate()
        self.last_monday = self.today.addDays(-self.today.dayOfWeek() + 1)

        self.setObjectName("NannyPayrollManager")
        self.setWindowTitle(self.UI_NAME)

        self.employee = None
        self.date_1_overlap = False
        self.date_2_overlap = False
        self.date_3_overlap = False
        self.date_4_overlap = False
        self.date_5_overlap = False

        self.cbx_employee = None
        self.chk_time_1 = None
        self.dte_time_1 = None
        self.spn_time_hours_1 = None
        self.cbx_time_1 = None
        self.spn_time_reimburse_1 = None
        self.lne_time_1 = None
        self.chk_time_2 = None
        self.dte_time_2 = None
        self.spn_time_hours_2 = None
        self.cbx_time_2 = None
        self.spn_time_reimburse_2 = None
        self.lne_time_2 = None
        self.chk_time_3 = None
        self.dte_time_3 = None
        self.spn_time_hours_3 = None
        self.cbx_time_3 = None
        self.spn_time_reimburse_3 = None
        self.lne_time_3 = None
        self.chk_time_4 = None
        self.dte_time_4 = None
        self.spn_time_hours_4 = None
        self.cbx_time_4 = None
        self.spn_time_reimburse_4 = None
        self.lne_time_4 = None
        self.chk_time_5 = None
        self.dte_time_5 = None
        self.spn_time_hours_5 = None
        self.cbx_time_5 = None
        self.spn_time_reimburse_5 = None
        self.lne_time_5 = None
        self.btn_save_time = None

        self.build_ui()
        self.populate_ui()

    def build_ui(self):
        self.resize(993, 460)

        # main widget and layout
        wdg_main = QtWidgets.QWidget()
        self.setCentralWidget(wdg_main)
        lyo_main = QtWidgets.QVBoxLayout(wdg_main)
        lyo_main.setContentsMargins(15, 12, 15, 15)
        lyo_main.setSpacing(9)

        # employee selector and today's date
        lyo_header = QtWidgets.QHBoxLayout()
        lyo_header.addWidget(QtWidgets.QLabel("Employee:"))
        self.cbx_employee = QtWidgets.QComboBox()
        self.cbx_employee.setMinimumWidth(150)
        self.cbx_employee.currentIndexChanged.connect(self.on_employee_changed)
        lyo_header.addWidget(self.cbx_employee)
        lyo_main.addLayout(lyo_header)
        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        lyo_header.addItem(spacer)
        lyo_header.addWidget(QtWidgets.QLabel(f"Today\'s Date:  {self.today.toPython().strftime('%m/%d/%Y')}"))

        lyo_body = QtWidgets.QHBoxLayout()
        lyo_main.addLayout(lyo_body)

        # enter time group box
        gbox_enter_time = QtWidgets.QGroupBox("Enter Time")
        lyo_body.addWidget(gbox_enter_time)
        lyo_enter_time = QtWidgets.QVBoxLayout(gbox_enter_time)

        lyo_time_grid = QtWidgets.QGridLayout()
        lyo_enter_time.addLayout(lyo_time_grid)

        # labels
        lyo_time_grid.addWidget(QtWidgets.QLabel("Date"), 0, 1)
        lyo_time_grid.addWidget(QtWidgets.QLabel("Hours"), 0, 2)
        lyo_time_grid.addWidget(QtWidgets.QLabel("Pay Type"), 0, 3)
        lyo_time_grid.addWidget(QtWidgets.QLabel("Reimbursement"), 0, 4)
        lyo_time_grid.addWidget(QtWidgets.QLabel("Notes"), 0, 5)

        # enter time day 1
        self.chk_time_1 = QtWidgets.QCheckBox()
        self.chk_time_1.setChecked(True)
        self.chk_time_1.stateChanged.connect(self.on_time_1_checked)
        lyo_time_grid.addWidget(self.chk_time_1, 1, 0)
        self.dte_time_1 = QtWidgets.QDateEdit()
        self.dte_time_1.setCalendarPopup(True)
        self.dte_time_1.dateChanged.connect(self.on_date_1_updated)
        lyo_time_grid.addWidget(self.dte_time_1, 1, 1)
        self.spn_time_hours_1 = QtWidgets.QDoubleSpinBox()
        self.spn_time_hours_1.setMinimumWidth(70)
        self.spn_time_hours_1.setDecimals(2)
        self.spn_time_hours_1.setSingleStep(0.25)
        self.spn_time_hours_1.setMinimum(0)
        self.spn_time_hours_1.setMaximum(24)
        self.spn_time_hours_1.setValue(8)
        lyo_time_grid.addWidget(self.spn_time_hours_1, 1, 2)
        self.cbx_time_1 = QtWidgets.QComboBox()
        lyo_time_grid.addWidget(self.cbx_time_1, 1, 3)
        self.spn_time_reimburse_1 = QtWidgets.QDoubleSpinBox()
        self.spn_time_reimburse_1.setDecimals(2)
        self.spn_time_reimburse_1.setSingleStep(0.01)
        self.spn_time_reimburse_1.setPrefix("$")
        self.spn_time_reimburse_1.setMinimum(-999999)
        self.spn_time_reimburse_1.setMaximum(999999)
        lyo_time_grid.addWidget(self.spn_time_reimburse_1, 1, 4)
        self.lne_time_1 = QtWidgets.QLineEdit()
        lyo_time_grid.addWidget(self.lne_time_1, 1, 5)

        # enter time day 2
        self.chk_time_2 = QtWidgets.QCheckBox()
        self.chk_time_2.setChecked(True)
        self.chk_time_2.stateChanged.connect(self.on_time_2_checked)
        lyo_time_grid.addWidget(self.chk_time_2, 2, 0)
        self.dte_time_2 = QtWidgets.QDateEdit()
        self.dte_time_2.setCalendarPopup(True)
        self.dte_time_2.dateChanged.connect(self.on_date_2_update)
        lyo_time_grid.addWidget(self.dte_time_2, 2, 1)
        self.spn_time_hours_2 = QtWidgets.QDoubleSpinBox()
        self.spn_time_hours_2.setMinimumWidth(70)
        self.spn_time_hours_2.setDecimals(2)
        self.spn_time_hours_2.setSingleStep(0.25)
        self.spn_time_hours_2.setMinimum(0)
        self.spn_time_hours_2.setMaximum(24)
        self.spn_time_hours_2.setValue(8)
        lyo_time_grid.addWidget(self.spn_time_hours_2, 2, 2)
        self.cbx_time_2 = QtWidgets.QComboBox()
        lyo_time_grid.addWidget(self.cbx_time_2, 2, 3)
        self.spn_time_reimburse_2 = QtWidgets.QDoubleSpinBox()
        self.spn_time_reimburse_2.setDecimals(2)
        self.spn_time_reimburse_2.setSingleStep(0.01)
        self.spn_time_reimburse_2.setPrefix("$")
        self.spn_time_reimburse_2.setMinimum(-999999)
        self.spn_time_reimburse_2.setMaximum(999999)
        lyo_time_grid.addWidget(self.spn_time_reimburse_2, 2, 4)
        self.lne_time_2 = QtWidgets.QLineEdit()
        lyo_time_grid.addWidget(self.lne_time_2, 2, 5)

        # enter time day 3
        self.chk_time_3 = QtWidgets.QCheckBox()
        self.chk_time_3.setChecked(True)
        self.chk_time_3.stateChanged.connect(self.on_time_3_checked)
        lyo_time_grid.addWidget(self.chk_time_3, 3, 0)
        self.dte_time_3 = QtWidgets.QDateEdit()
        self.dte_time_3.setCalendarPopup(True)
        self.dte_time_3.dateChanged.connect(self.on_date_3_update)
        lyo_time_grid.addWidget(self.dte_time_3, 3, 1)
        self.spn_time_hours_3 = QtWidgets.QDoubleSpinBox()
        self.spn_time_hours_3.setMinimumWidth(70)
        self.spn_time_hours_3.setDecimals(2)
        self.spn_time_hours_3.setSingleStep(0.25)
        self.spn_time_hours_3.setMinimum(0)
        self.spn_time_hours_3.setMaximum(24)
        self.spn_time_hours_3.setValue(8)
        lyo_time_grid.addWidget(self.spn_time_hours_3, 3, 2)
        self.cbx_time_3 = QtWidgets.QComboBox()
        lyo_time_grid.addWidget(self.cbx_time_3, 3, 3)
        self.spn_time_reimburse_3 = QtWidgets.QDoubleSpinBox()
        self.spn_time_reimburse_3.setDecimals(2)
        self.spn_time_reimburse_3.setSingleStep(0.01)
        self.spn_time_reimburse_3.setPrefix("$")
        self.spn_time_reimburse_3.setMinimum(-999999)
        self.spn_time_reimburse_3.setMaximum(999999)
        lyo_time_grid.addWidget(self.spn_time_reimburse_3, 3, 4)
        self.lne_time_3 = QtWidgets.QLineEdit()
        lyo_time_grid.addWidget(self.lne_time_3, 3, 5)

        # enter time day 3
        self.chk_time_4 = QtWidgets.QCheckBox()
        self.chk_time_4.setChecked(True)
        self.chk_time_4.stateChanged.connect(self.on_time_4_checked)
        lyo_time_grid.addWidget(self.chk_time_4, 4, 0)
        self.dte_time_4 = QtWidgets.QDateEdit()
        self.dte_time_4.setCalendarPopup(True)
        self.dte_time_4.dateChanged.connect(self.on_date_4_update)
        lyo_time_grid.addWidget(self.dte_time_4, 4, 1)
        self.spn_time_hours_4 = QtWidgets.QDoubleSpinBox()
        self.spn_time_hours_4.setMinimumWidth(70)
        self.spn_time_hours_4.setDecimals(2)
        self.spn_time_hours_4.setSingleStep(0.25)
        self.spn_time_hours_4.setMinimum(0)
        self.spn_time_hours_4.setMaximum(24)
        self.spn_time_hours_4.setValue(8)
        lyo_time_grid.addWidget(self.spn_time_hours_4, 4, 2)
        self.cbx_time_4 = QtWidgets.QComboBox()
        lyo_time_grid.addWidget(self.cbx_time_4, 4, 3)
        self.spn_time_reimburse_4 = QtWidgets.QDoubleSpinBox()
        self.spn_time_reimburse_4.setDecimals(2)
        self.spn_time_reimburse_4.setSingleStep(0.01)
        self.spn_time_reimburse_4.setPrefix("$")
        self.spn_time_reimburse_4.setMinimum(-999999)
        self.spn_time_reimburse_4.setMaximum(999999)
        lyo_time_grid.addWidget(self.spn_time_reimburse_4, 4, 4)
        self.lne_time_4 = QtWidgets.QLineEdit()
        lyo_time_grid.addWidget(self.lne_time_4, 4, 5)

        # enter time day 5
        self.chk_time_5 = QtWidgets.QCheckBox()
        self.chk_time_5.setChecked(True)
        self.chk_time_5.stateChanged.connect(self.on_time_5_checked)
        lyo_time_grid.addWidget(self.chk_time_5, 5, 0)
        self.dte_time_5 = QtWidgets.QDateEdit()
        self.dte_time_5.setCalendarPopup(True)
        self.dte_time_5.dateChanged.connect(self.on_date_5_update)
        lyo_time_grid.addWidget(self.dte_time_5, 5, 1)
        self.spn_time_hours_5 = QtWidgets.QDoubleSpinBox()
        self.spn_time_hours_5.setMinimumWidth(70)
        self.spn_time_hours_5.setDecimals(2)
        self.spn_time_hours_5.setSingleStep(0.25)
        self.spn_time_hours_5.setMinimum(0)
        self.spn_time_hours_5.setMaximum(24)
        self.spn_time_hours_5.setValue(8)
        lyo_time_grid.addWidget(self.spn_time_hours_5, 5, 2)
        self.cbx_time_5 = QtWidgets.QComboBox()
        lyo_time_grid.addWidget(self.cbx_time_5, 5, 3)
        self.spn_time_reimburse_5 = QtWidgets.QDoubleSpinBox()
        self.spn_time_reimburse_5.setDecimals(2)
        self.spn_time_reimburse_5.setSingleStep(0.01)
        self.spn_time_reimburse_5.setPrefix("$")
        self.spn_time_reimburse_5.setMinimum(-999999)
        self.spn_time_reimburse_5.setMaximum(999999)
        lyo_time_grid.addWidget(self.spn_time_reimburse_5, 5, 4)
        self.lne_time_5 = QtWidgets.QLineEdit()
        lyo_time_grid.addWidget(self.lne_time_5, 5, 5)

        # spacer and save button
        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        lyo_enter_time.addItem(spacer)
        self.btn_save_time = QtWidgets.QPushButton("Save Time Entries")
        self.btn_save_time.clicked.connect(self.on_save)
        lyo_enter_time.addWidget(self.btn_save_time)

        # reports layout
        lyo_reports = QtWidgets.QVBoxLayout()
        lyo_body.addLayout(lyo_reports)

        gbx_timesheet = QtWidgets.QGroupBox("Timesheets")
        lyo_reports.addWidget(gbx_timesheet)
        lyo_timesheet = QtWidgets.QVBoxLayout(gbx_timesheet)
        lyo_timesheet_dates = QtWidgets.QHBoxLayout()
        lyo_timesheet.addLayout(lyo_timesheet_dates)

        lyo_timesheet_dates.addWidget(QtWidgets.QLabel("Start Date:"))
        self.dte_timesheet_start = QtWidgets.QDateEdit()
        self.dte_timesheet_start.setCalendarPopup(True)
        self.dte_timesheet_start.dateChanged.connect(self.on_timesheet_start_update)
        lyo_timesheet_dates.addWidget(self.dte_timesheet_start)
        lyo_timesheet_dates.addWidget(QtWidgets.QLabel("End Date:"))
        self.dte_timesheet_end = QtWidgets.QDateEdit()
        self.dte_timesheet_end.setCalendarPopup(True)
        self.dte_timesheet_end.dateChanged.connect(self.update_timesheet_path)
        lyo_timesheet_dates.addWidget(self.dte_timesheet_end)

        lyo_timesheet_path = QtWidgets.QHBoxLayout()
        lyo_timesheet.addLayout(lyo_timesheet_path)
        self.lne_timesheet_path = QtWidgets.QLineEdit()
        lyo_timesheet_path.addWidget(self.lne_timesheet_path)
        self.btn_timesheet_path = QtWidgets.QPushButton("...")
        self.btn_timesheet_path.setMaximumWidth(30)
        self.btn_timesheet_path.clicked.connect(self.on_btn_timesheet_path)
        lyo_timesheet_path.addWidget(self.btn_timesheet_path)

        self.btn_timesheet_save = QtWidgets.QPushButton("Save Timesheet as PDF")
        self.btn_timesheet_save.clicked.connect(self.on_save_timesheet)
        lyo_timesheet.addWidget(self.btn_timesheet_save)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        lyo_reports.addItem(spacer)

    def populate_ui(self):
        self.cbx_employee.addItems(self.data.employee_names)
        self.dte_time_1.setDate(self.last_monday)
        self.dte_time_2.setDate(self.last_monday.addDays(1))
        self.dte_time_3.setDate(self.last_monday.addDays(2))
        self.dte_time_4.setDate(self.last_monday.addDays(3))
        self.dte_time_5.setDate(self.last_monday.addDays(4))

        # populate time types
        pay_types = [pay_type.name.replace('_', ' ').title() for pay_type in data_provider.PayType]
        self.cbx_time_1.addItems(pay_types)
        self.cbx_time_2.addItems(pay_types)
        self.cbx_time_3.addItems(pay_types)
        self.cbx_time_4.addItems(pay_types)
        self.cbx_time_5.addItems(pay_types)

        # autofill holidays
        self.check_for_holidays(self.dte_time_1, self.cbx_time_1, self.lne_time_1)
        self.check_for_holidays(self.dte_time_2, self.cbx_time_2, self.lne_time_2)
        self.check_for_holidays(self.dte_time_3, self.cbx_time_3, self.lne_time_3)
        self.check_for_holidays(self.dte_time_4, self.cbx_time_4, self.lne_time_4)
        self.check_for_holidays(self.dte_time_5, self.cbx_time_5, self.lne_time_5)

        # autofill timesheet
        self.dte_timesheet_start.setDate(self.last_monday)
        self.dte_timesheet_end.setDate(self.last_monday.addDays(4))
        self.update_timesheet_path()

    def update_timesheet_path(self):
        employee = self.data.get_employee_from_name(self.cbx_employee.currentText())
        end_date = self.dte_timesheet_end.date()
        timesheet_path = config.TIMESHEET_DIR / f"Payroll_{employee.name.replace(' ', '')}_{end_date.toPython().isoformat()}.pdf"
        self.lne_timesheet_path.setText(str(timesheet_path))

    def check_for_holidays(self, date_wdg: QtWidgets.QDateEdit, type_wdg: QtWidgets.QComboBox, note_wdg: QtWidgets.QLineEdit):
        match = False
        for holiday in self.data.paid_holidays:
            if date_wdg.date().toPython() == holiday.date:
                type_wdg.setCurrentIndex(data_provider.PayType.PAID_HOLIDAY.value)
                note_wdg.setText(holiday.name)
                match = True

        if not match:
            type_wdg.setCurrentIndex(0)
            note_wdg.clear()

    def check_for_overlapping_dates(self, date_widget):
        """Colors any time entry dates that already exist for the selected employee."""
        overlap = False
        date = date_widget.date().toPython()
        for time_entry in self.employee.time_entries:
            if date == time_entry.date:
                overlap = True
                break

        if overlap:
            date_widget.setStyleSheet("QDateEdit{color: red;}")
            date_widget.setToolTip("There is already a time entry on this date.")
        else:
            date_widget.setStyleSheet("")
            date_widget.setToolTip("")

        return overlap

    def on_employee_changed(self):
        self.employee = self.data.get_employee_from_name(self.cbx_employee.currentText())
        self.update_timesheet_path()
        if self.check_for_overlapping_dates(self.dte_time_1):
            self.date_1_overlap = True
            self.chk_time_1.setChecked(False)  # FIXME not working
        if self.check_for_overlapping_dates(self.dte_time_2):
            self.date_2_overlap = True
            self.chk_time_2.setChecked(False)
        if self.check_for_overlapping_dates(self.dte_time_3):
            self.date_3_overlap = True
            self.chk_time_3.setChecked(False)
        if self.check_for_overlapping_dates(self.dte_time_4):
            self.date_4_overlap = True
            self.chk_time_4.setChecked(False)
        if self.check_for_overlapping_dates(self.dte_time_5):
            self.date_5_overlap = True
            self.chk_time_5.setChecked(False)

    def on_time_1_checked(self):
        is_enabled = self.chk_time_1.isChecked()
        self.dte_time_1.setEnabled(is_enabled)
        self.spn_time_hours_1.setEnabled(is_enabled)
        self.cbx_time_1.setEnabled(is_enabled)
        self.spn_time_reimburse_1.setEnabled(is_enabled)
        self.lne_time_1.setEnabled(is_enabled)

    def on_time_2_checked(self):
        is_enabled = self.chk_time_2.isChecked()
        self.dte_time_2.setEnabled(is_enabled)
        self.spn_time_hours_2.setEnabled(is_enabled)
        self.cbx_time_2.setEnabled(is_enabled)
        self.spn_time_reimburse_2.setEnabled(is_enabled)
        self.lne_time_2.setEnabled(is_enabled)

    def on_time_3_checked(self):
        is_enabled = self.chk_time_3.isChecked()
        self.dte_time_3.setEnabled(is_enabled)
        self.spn_time_hours_3.setEnabled(is_enabled)
        self.cbx_time_3.setEnabled(is_enabled)
        self.spn_time_reimburse_3.setEnabled(is_enabled)
        self.lne_time_3.setEnabled(is_enabled)

    def on_time_4_checked(self):
        is_enabled = self.chk_time_4.isChecked()
        self.dte_time_4.setEnabled(is_enabled)
        self.spn_time_hours_4.setEnabled(is_enabled)
        self.cbx_time_4.setEnabled(is_enabled)
        self.spn_time_reimburse_4.setEnabled(is_enabled)
        self.lne_time_4.setEnabled(is_enabled)

    def on_time_5_checked(self):
        is_enabled = self.chk_time_5.isChecked()
        self.dte_time_5.setEnabled(is_enabled)
        self.spn_time_hours_5.setEnabled(is_enabled)
        self.cbx_time_5.setEnabled(is_enabled)
        self.spn_time_reimburse_5.setEnabled(is_enabled)
        self.lne_time_5.setEnabled(is_enabled)

    def on_date_1_updated(self):
        """When the first date is changed, update all the subsequent ones."""
        first_date = self.dte_time_1.date()
        self.dte_time_2.setDate(first_date.addDays(1))
        self.dte_time_3.setDate(first_date.addDays(2))
        self.dte_time_4.setDate(first_date.addDays(3))
        self.dte_time_5.setDate(first_date.addDays(4))

        self.check_for_holidays(self.dte_time_1, self.cbx_time_1, self.lne_time_1)
        self.date_1_overlap = self.check_for_overlapping_dates(self.dte_time_1)

    def on_date_2_update(self):
        self.check_for_holidays(self.dte_time_2, self.cbx_time_2, self.lne_time_2)
        self.date_2_overlap = self.check_for_overlapping_dates(self.dte_time_2)

    def on_date_3_update(self):
        self.check_for_holidays(self.dte_time_3, self.cbx_time_3, self.lne_time_3)
        self.date_3_overlap = self.check_for_overlapping_dates(self.dte_time_3)

    def on_date_4_update(self):
        self.check_for_holidays(self.dte_time_4, self.cbx_time_4, self.lne_time_4)
        self.date_4_overlap = self.check_for_overlapping_dates(self.dte_time_4)

    def on_date_5_update(self):
        self.check_for_holidays(self.dte_time_5, self.cbx_time_5, self.lne_time_5)
        self.date_5_overlap = self.check_for_overlapping_dates(self.dte_time_5)

    def add_time_from_ui(
        self,
        date_wdg: QtWidgets.QDateEdit,
        hours_wdg: QtWidgets.QDoubleSpinBox,
        type_wdg: QtWidgets.QComboBox,
        reimbursement_wdg: QtWidgets.QDoubleSpinBox,
        note_wdg: QtWidgets.QLineEdit
    ):
        date = date_wdg.date().toPython()
        hours = hours_wdg.value()
        type_str = type_wdg.currentText().replace(' ', '_').upper()
        pay_type = data_provider.PayType[type_str]
        reimbursement = reimbursement_wdg.value() if reimbursement_wdg.value() != 0 else None
        note = note_wdg.text() if note_wdg.text() else None

        # validate input
        if hours == 0 and reimbursement is None:
            print(f"WARNING: Unable to add 0 time for '{date.strftime('%m/%d/%Y')}'")
            return

        # add the time entry
        self.data.add_worked_time(date, self.employee, hours, pay_type, reimbursement, note)

    def on_save(self):
        """Collects the data from the Enter Time fields and writes them to disk for the selected employee."""
        # if any of the chosen dates overlap existing time entries, ask the user if they want to proceed
        # TODO check if any date widgets share a date and warn about overlaps
        overlaps_to_check = []
        if self.chk_time_1.isChecked():
            overlaps_to_check.append(self.date_1_overlap)
        if self.chk_time_2.isChecked():
            overlaps_to_check.append(self.date_2_overlap)
        if self.chk_time_3.isChecked():
            overlaps_to_check.append(self.date_3_overlap)
        if self.chk_time_4.isChecked():
            overlaps_to_check.append(self.date_4_overlap)
        if self.chk_time_5.isChecked():
            overlaps_to_check.append(self.date_5_overlap)
        if any(overlaps_to_check):
            flags = QtWidgets.QMessageBox.StandardButton.Yes
            flags |= QtWidgets.QMessageBox.StandardButton.Cancel
            question = "Are you sure you want to add time entries on the same date as existing entries?"
            response = QtWidgets.QMessageBox.question(self, "Add Overlapping Date?", question, flags)
            if response != QtWidgets.QMessageBox.Yes:
                return

        if self.chk_time_1.isChecked():
            self.add_time_from_ui(self.dte_time_1, self.spn_time_hours_1, self.cbx_time_1, self.spn_time_reimburse_1, self.lne_time_1)
        if self.chk_time_2.isChecked():
            self.add_time_from_ui(self.dte_time_2, self.spn_time_hours_2, self.cbx_time_2, self.spn_time_reimburse_2, self.lne_time_2)
        if self.chk_time_3.isChecked():
            self.add_time_from_ui(self.dte_time_3, self.spn_time_hours_3, self.cbx_time_3, self.spn_time_reimburse_3, self.lne_time_3)
        if self.chk_time_4.isChecked():
            self.add_time_from_ui(self.dte_time_4, self.spn_time_hours_4, self.cbx_time_4, self.spn_time_reimburse_4, self.lne_time_4)
        if self.chk_time_5.isChecked():
            self.add_time_from_ui(self.dte_time_5, self.spn_time_hours_5, self.cbx_time_5, self.spn_time_reimburse_5, self.lne_time_5)

        success = self.data.save()

        # message box
        msg_box = QtWidgets.QMessageBox()
        if success:
            msg_box.setText("Time entries saved successfully.")
        else:
            msg_box.setText("WARNING: Nothing to save.")
        msg_box.exec_()

    def on_timesheet_start_update(self):
        start = self.dte_timesheet_start.date()
        end = self.dte_timesheet_end.date()
        if end <= start:
            self.dte_timesheet_end.setDate(start.addDays(1))

    def on_btn_timesheet_path(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, "Select Path", str(config.TIMESHEET_DIR), "PDF File (*.pdf)")
        if file_name[0]:
            self.lne_timesheet_path.setText(file_name[0])

    def on_save_timesheet(self):
        start = self.dte_timesheet_start.date().toPython()
        end = self.dte_timesheet_end.date().toPython()
        path_str = self.lne_timesheet_path.text()
        employee = self.data.get_employee_from_name(self.cbx_employee.currentText())

        msg_box = QtWidgets.QMessageBox()

        # validate input
        if end <= start:
            msg_box.setText("ERROR: Invalid date range. The end date must be after the start date.")
            msg_box.exec()
            return
        if not path_str:
            msg_box.setText("ERROR: No path provided.")
            msg_box.exec()
            return

        timesheet_path = Path(path_str)
        timesheet_path.parent.mkdir(parents=True, exist_ok=True)

        timesheet = reports.Timesheet(self.data, employee, start_date=start, end_date=end)
        timesheet.to_pdf(timesheet_path)

        msg_box.setText("Timesheet saved.")
        msg_box.exec()
