
__author__ = 'Sean Kraft'

from datetime import date as Date
from pathlib import Path
from enum import Enum
import config
import shutil
import json


class DuplicateEntryError(Exception):
    pass


class DataProviderError(Exception):
    pass


class DataProviderWarning(Exception):
    pass


class PayType(Enum):
    REGULAR = 0
    PAID_TIME_OFF = 1
    PAID_HOLIDAY = 2
    PAID_SICK_TIME = 3
    UNPAID_TIME_OFF = 4  # FIXME Not implemented


class TaxRates:
    def __init__(self, **kwargs):
        self.year: int = kwargs.get("year")
        self.medicare_employee: int or float = kwargs.get("medicare_employee")  # percent value: ie 1.45%
        self.medicare_company: int or float = kwargs.get("medicare_company")  # percent value: ie 1.45%
        self.ss_employee: int or float = kwargs.get("ss_employee")  # percent value: ie 1.45%
        self.ss_company: int or float = kwargs.get("ss_company")  # percent value: ie 1.45%
        self.paid_fml: int or float = kwargs.get("paid_fml")  # percent value: ie 1.45%
        self.federal_unemployment: int or float = kwargs.get("federal_unemployment")  # percent value: ie 1.45%
        self.federal_unemployment_hour_cap: int = kwargs.get("federal_unemployment_hour_cap")
        self.state_unemployment: int or float = kwargs.get("state_unemployment")  # percent value: ie 1.45%

    def __repr__(self):
        return f"TaxRates(year={self.year})"


class Employer:
    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name")
        self.ein: str = kwargs.get("ein")
        self.business_id: str = kwargs.get("business_id")
        self.address_line_1: str = kwargs.get("address_line_1")
        self.address_line_2: str = kwargs.get("address_line_2")
        self.address_line_3: str = kwargs.get("address_line_3")

    @property
    def address(self):
        address = self.address_line_1
        if self.address_line_2:
            address = f"{address}, {self.address_line_2}"
        if self.address_line_3:
            address = f"{address}, {self.address_line_3}"
        return address

    @property
    def address_multiline(self):
        address = self.address_line_1
        if self.address_line_2:
            address = f"{address}\n{self.address_line_2}"
        if self.address_line_3:
            address = f"{address}\n{self.address_line_3}"
        return address

    def __repr__(self):
        return f"Employer(name={self.name}, address={self.address})"


class Employee:
    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name")
        self.ssn: str = kwargs.get("ssn")
        self.pay_rate: int or float = kwargs.get("pay_rate")
        self.paid_vacation: int or float = kwargs.get("paid_vacation")  # in hours
        self.paid_sick: int or float = kwargs.get("paid_sick")  # in hours
        self.paid_holidays: int or float = kwargs.get("paid_holidays")  # in hours
        self.address_line_1: str = kwargs.get("address_line_1")
        self.address_line_2: str = kwargs.get("address_line_2")
        self.address_line_3: str = kwargs.get("address_line_3")
        self.time_entries: list[TimeEntry] = []

        self.appdata_path: Path = None

    @property
    def address(self):
        address = self.address_line_1
        if self.address_line_2:
            address = f"{address}, {self.address_line_2}"
        if self.address_line_3:
            address = f"{address}, {self.address_line_3}"
        return address

    @property
    def address_multiline(self):
        address = self.address_line_1
        if self.address_line_2:
            address = f"{address}\n{self.address_line_2}"
        if self.address_line_3:
            address = f"{address}\n{self.address_line_3}"
        return address

    def __repr__(self):
        return f"Employee(name={self.name}, pay_rate={self.pay_rate})"


class TimeEntry:
    def __init__(self, **kwargs):
        self.date: Date = kwargs.get("date")
        self.employee: str = kwargs.get("employee")
        self.tax_year: int = kwargs.get("tax_year")
        self.hours: int or float = kwargs.get("hours")
        self.pay_rate: int or float = kwargs.get("pay_rate")
        self.pay_type: PayType = kwargs.get("pay_type", PayType.REGULAR)
        self.reimbursement: int or float = kwargs.get("reimbursement", 0)  # optional: milage or general reimbursements
        self.note: str = kwargs.get('note')

        self.tax_rates: TaxRates = None

    def __repr__(self):
        return f"TimeEntry(date={self.date}, employee={self.employee}, tax_year={self.tax_year}, " \
               f"hours={self.hours}, pay_rate={self.pay_rate}, pay_type={self.pay_type})"

    @property
    def gross_pay(self) -> float:
        """Returns the gross pay from this time entry."""
        try:
            return self._gross_pay
        except AttributeError:
            self._gross_pay = self.pay_rate * self.hours
            return self._gross_pay

    @property
    def medicare_employee(self) -> float:
        """Returns the medicare employee withholding amount. (self.tax_rates must be populated)"""
        try:
            return self._medicare_employee
        except AttributeError:
            self._medicare_employee = self.gross_pay * (self.tax_rates.medicare_employee / 100)
            return self._medicare_employee

    @property
    def medicare_company(self) -> float:
        """Returns the medicare company contribution amount. (self.tax_rates must be populated)"""
        try:
            return self._medicare_company
        except AttributeError:
            self._medicare_company = self.gross_pay * (self.tax_rates.medicare_company / 100)
            return self._medicare_company

    @property
    def ss_employee(self) -> float:
        """Returns the social security employee withholding amount. (self.tax_rates must be populated)"""
        try:
            return self._ss_employee
        except AttributeError:
            self._ss_employee = self.gross_pay * (self.tax_rates.ss_employee / 100)
            return self._ss_employee

    @property
    def ss_company(self) -> float:
        """Returns the social security company contribution amount. (self.tax_rates must be populated)"""
        try:
            return self._ss_company
        except AttributeError:
            self._ss_company = self.gross_pay * (self.tax_rates.ss_company / 100)
            return self._ss_company

    @property
    def paid_fml(self) -> float:
        """Returns the WA paid family and medical leave withholding amount. (self.tax_rates must be populated)"""
        try:
            return self._paid_fml
        except AttributeError:
            self._paid_fml = self.gross_pay * (self.tax_rates.paid_fml / 100)
            return self._paid_fml

    @property
    def employee_taxes_withheld(self) -> float:
        """Returns the total employee taxes withheld. (self.tax_rates must be populated)"""
        try:
            return self._employee_taxes_withheld
        except AttributeError:
            self._employee_taxes_withheld = self.medicare_employee + self.ss_employee + self.paid_fml
            return self._employee_taxes_withheld

    @property
    def net_pay(self) -> float:
        """Returns the employees pay after tax withholdings (not including reimbursements)."""
        try:
            return self._net_pay
        except AttributeError:
            self._net_pay = self.gross_pay - self.employee_taxes_withheld
            return self._net_pay

    @property
    def check_amount(self) -> float:
        """Returns the employees take home pay."""
        return self.net_pay + self.reimbursement

    @property
    def federal_unemployment(self) -> float:
        """Returns the federal unemployment company contribution amount."""
        try:
            return self._federal_unemployment
        except AttributeError:
            self._federal_unemployment = self.gross_pay * (self.tax_rates.federal_unemployment / 100)
            return self._federal_unemployment

    @property
    def state_unemployment(self) -> float:
        """Returns the state unemployment company contribution amount."""
        try:
            return self._state_unemployment
        except AttributeError:
            self._state_unemployment = self.gross_pay * (self.tax_rates.state_unemployment / 100)
            return self._state_unemployment

    @property
    def company_tax_contributions(self) -> float:
        try:
            return self._company_tax_contributions
        except AttributeError:
            self._company_tax_contributions = (self.medicare_company +
                                               self.ss_company +
                                               self.federal_unemployment +
                                               self.state_unemployment)
            return self._company_tax_contributions

    @property
    def company_total_costs(self) -> float:
        return self.gross_pay + self.company_tax_contributions + self.reimbursement

    def as_dictionary(self):
        """Returns the TimeEntry data as a dictionary. (so it can be written to json)."""
        out_dict = {
                "Date": self.date.isoformat(),
                "Employee": self.employee,
                "TaxYear": self.tax_year,
                "Hours": self.hours,
                "PayRate": self.pay_rate,
                "PayType": self.pay_type.value,
                }
        if self.reimbursement:
            out_dict["Reimbursement"] = self.reimbursement
        if self.note:
            out_dict["Note"] = self.note
        return out_dict

    def populate_from_dictionary(self, in_dict):
        """Populates the class data from a provided dictionary. (so it can be loaded from json)"""
        self.date = Date.fromisoformat(in_dict["Date"])
        self.employee = in_dict["Employee"]
        self.tax_year = in_dict["TaxYear"]
        self.hours = in_dict["Hours"]
        self.pay_rate = in_dict["PayRate"]
        self.pay_type = PayType(in_dict["PayType"])
        self.reimbursement = in_dict.get("Reimbursement", 0)  # this is an optional field
        self.note = in_dict.get("Note")  # this is an optional field


class DataProvider:
    def __init__(self):

        self.first_run = False

        self.tax_rates = []
        self.employer = Employer()
        self.employees = []

        # if required appdata folders don't exist, create them and populate stub data
        self.init_appdata_dir()

        self.load_tax_rate_data()
        self.load_employer_data()
        self.load_employee_data()
        self.load_timesheet_data()

    def init_appdata_dir(self):
        """If the appdata directory doesn't already exist, this function populates it with stub data."""
        # if the application data directory does not exist, create it and populate stub data
        if not config.TAX_RATES_FILE.exists():
            config.APP_DATA_DIR.mkdir(parents=True)
            shutil.copy(config.STUB_TAX_RATES_FILE, config.TAX_RATES_FILE)
            self.first_run = True

        if not config.EMPLOYER_FILE.exists():
            shutil.copy(config.STUB_EMPLOYER_FILE, config.EMPLOYER_FILE)
            self.first_run = True

        if not config.EMPLOYEES_DIR.exists():
            config.EMPLOYEES_DIR.mkdir()
            self.first_run = True

        if self.first_run:
            raise UserWarning('Populate tax rate, employer, and employee data before starting the tool.')

    def load_tax_rate_data(self):
        """Reads all tax rate entries from the appdata directory and serializes them."""
        with open(config.TAX_RATES_FILE) as inFile:
            tax_rates = json.load(inFile)

            for rates in tax_rates:
                tax_rate = TaxRates()
                tax_rate.year = rates["TaxYear"]
                tax_rate.medicare_employee = rates["MedicareEmployee"]
                tax_rate.medicare_company = rates["MedicareCompany"]
                tax_rate.ss_employee = rates["SocialSecurityEmployee"]
                tax_rate.ss_company = rates["SocialSecurityCompany"]
                tax_rate.paid_fml = rates["PaidFamilyMedicalLeave"]
                tax_rate.federal_unemployment = rates["FederalUnemployment"]
                tax_rate.federal_unemployment_hour_cap = rates["FederalUnemploymentHourCap"]
                tax_rate.state_unemployment = rates["StateUnemployment"]

                self.tax_rates.append(tax_rate)

    def load_employer_data(self):
        """Reads the employer data from the appdata directory and serializes it."""
        with open(config.EMPLOYER_FILE) as inFile:
            employer = json.load(inFile)
            self.employer.name = employer["Name"]
            self.employer.ein = employer["EIN"]
            self.employer.business_id = employer["BusinessID"]
            self.employer.address_line_1 = employer["AddressLine1"]
            self.employer.address_line_2 = employer["AddressLine2"]
            self.employer.address_line_3 = employer["AddressLine3"]

    def load_employee_data(self):
        """Reads all employee entries from the appdata directory and serializes them."""
        employee_files = config.EMPLOYEES_DIR.glob('**/*.json')
        for employee_file in employee_files:
            # skip all but the base employee files  TODO this should be better?
            if "_" in employee_file.name:
                continue

            with open(employee_file) as infile:
                emp = json.load(infile)

                employee = Employee()
                employee.name = emp["Name"]
                employee.ssn = emp["SSN"]
                employee.pay_rate = emp["PayRate"]
                employee.paid_vacation = emp["PaidVacationHoursPerYear"]
                employee.paid_sick = emp["PaidSickHoursPerYear"]
                employee.paid_holidays = emp["PaidHolidayHoursPerYear"]
                employee.address_line_1 = emp["AddressLine1"]
                employee.address_line_2 = emp["AddressLine2"]
                employee.address_line_3 = emp["AddressLine3"]
                employee.appdata_path = employee_file

                self.employees.append(employee)

    def load_timesheet_data(self):
        """Reads all timesheet entries from the appdata directory and serializes them."""
        for employee in self.employees:
            employee_time_file = employee.appdata_path.parent / (employee.appdata_path.stem + "_TimeEntries.json")

            if employee_time_file.exists():
                with open(employee_time_file) as infile:
                    json_entries = json.load(infile)

                employee.time_entries = []
                for time_dict in json_entries:
                    time_entry = TimeEntry()
                    time_entry.populate_from_dictionary(time_dict)
                    employee.time_entries.append(time_entry)

    def make_new_employee(self, name: str):
        employee_name = name.replace(" ", "")
        employee_dir = config.EMPLOYEES_DIR / employee_name
        if employee_dir.exists():
            raise FileExistsError(f'A directory named {employee_name} already exists.')

        employee_dir.mkdir(parents=True)
        shutil.copy(config.STUB_EMPLOYEE_FILE, employee_dir / (employee_name + '.json'))

        # TODO this should write the name to the new json file

        self.load_employee_data()

    def get_tax_rates(self, year: int = None) -> TaxRates or None:
        """Returns the most recent tax rate year or a specific year if requested."""
        # return a specific year if requested
        if year:
            for tax_rate in self.tax_rates:
                if tax_rate.year == year:
                    return tax_rate
            return None

        # otherwise, return the most recent year
        else:
            current_rates = None
            for tax_rate in self.tax_rates:
                if current_rates is None or current_rates["TaxYear"] < tax_rate["TaxYear"]:
                    current_rates = tax_rate
            return current_rates

    def get_employee_from_name(self, employee_name: str) -> Employee:
        """Returns an employee object that matches the provided name."""
        for employee in self.employees:
            if employee.name == employee_name:
                return employee
        raise DataProviderError(f"No match for employee: '{employee_name}'")

    def add_worked_time(
        self,
        date: Date,
        employee: str or Employee,
        hours: int or float,
        pay_type: PayType = PayType.REGULAR,
        reimbursement: int or float = None,
        note: str = None
    ):
        """Adds a time entry to the provided employee's worked_time list."""
        if not isinstance(employee, Employee):
            employee = self.get_employee_from_name(employee)
        rates = self.get_tax_rates()

        # check if this date has already been entered (except reimbursements which can share the date)
        for time_entry in employee.time_entries:
            if date == time_entry.date:
                raise DuplicateEntryError(f"A time entry for {date} already exists for {employee.name}.")

        time_entry = TimeEntry()
        time_entry.date = date
        time_entry.employee = employee.name
        time_entry.tax_year = rates.year
        time_entry.hours = hours
        time_entry.pay_rate = employee.pay_rate
        time_entry.pay_type = pay_type
        if reimbursement is not None:
            time_entry.reimbursement = reimbursement
        if note:
            time_entry.note = note

        employee.time_entries.append(time_entry)

    def get_worked_time_in_range(self, employee: str or Employee, start_date: Date, end_date: Date) -> list[TimeEntry]:
        """Finds all time entries for the provided employee that match """
        if not isinstance(employee, Employee):
            employee = self.get_employee_from_name(employee)

        matches = []
        for time_entry in employee.time_entries:
            if start_date <= time_entry.date <= end_date:
                matches.append(time_entry)

        return matches

    def save(self):
        for employee in self.employees:
            employee_file_name = employee.name.replace(" ", "")
            file_path = config.EMPLOYEES_DIR / employee_file_name / f"{employee_file_name}_TimeEntries.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            all_time_entries = [time_entry.as_dictionary() for time_entry in employee.time_entries]
            with open(file_path, "w") as outfile:
                json.dump(all_time_entries, outfile, indent=2)

            print(f"{file_path} saved.")

