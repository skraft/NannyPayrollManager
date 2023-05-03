
__author__ = 'Sean Kraft'

from datetime import date as Date
from pathlib import Path
import config
import shutil
import json


class DuplicateEntryError(Exception):
    pass


class TaxRates:
    def __init__(self, **kwargs):
        self.year = kwargs.get("year")
        self.medicare_employee = kwargs.get("medicare_employee")
        self.medicare_company = kwargs.get("medicare_company")
        self.ss_employee = kwargs.get("ss_employee")
        self.ss_company = kwargs.get("ss_company")
        self.paid_fml = kwargs.get("paid_fml")
        self.federal_unemployment = kwargs.get("federal_unemployment")
        self.state_unemployment = kwargs.get("state_unemployment")

    def __repr__(self):
        return f"TaxRates(year={self.year})"


class Employee:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.ssn = kwargs.get("ssn")
        self.pay_rate = kwargs.get("pay_rate")
        self.paid_vacation = kwargs.get("paid_vacation")
        self.paid_sick = kwargs.get("paid_sick")
        self.paid_holidays = kwargs.get("paid_holidays")
        self.address = kwargs.get("address")
        self.time_entries = []

    def __repr__(self):
        return f"Employee(name={self.name}, pay_rate={self.pay_rate})"


class TimeEntry:
    def __init__(self, **kwargs):
        self.date = kwargs.get("date")
        self.employee = kwargs.get("employee")
        self.tax_year = kwargs.get("tax_year")
        self.hours = kwargs.get("hours")
        self.pay_rate = kwargs.get("pay_rate")

    def __repr__(self):
        return f"TimeEntry(date={self.date}, employee={self.employee}, tax_year={self.tax_year}, " \
               f"hours={self.hours}, pay_rate={self.pay_rate})"


class DataProvider:
    def __init__(self):

        self.first_run = False

        self.tax_rates = []
        self.employees = []

        # if required appdata folders don't exist, create them
        self.init_appdata_dir()

        # load all tax rate data
        self.load_tax_rate_data()

        # load all employee data
        self.load_employee_data()

        # load all timesheet data
        self.load_timesheet_data()

    def init_appdata_dir(self):
        """If the appdata directory doesn't already exist, this function populates it with stub data."""
        # if the application data directory does not exist, create it and populate stub data
        if not config.TAX_RATES_FILE.exists():
            config.APP_DATA_DIR.mkdir(parents=True)
            shutil.copy(config.STUB_TAX_RATES_FILE, config.TAX_RATES_FILE)
            self.first_run = True

        if not config.EMPLOYEES_DIR.exists():
            config.EMPLOYEES_DIR.mkdir()
            self.first_run = True

        if self.first_run:
            raise UserWarning('Populate tax rate and employee data before starting the tool.')

    def load_tax_rate_data(self):
        """Reads all tax rate entries from the appdata directory and serializes them."""
        if not config.TAX_RATES_FILE.exists():
            raise FileNotFoundError(config.TAX_RATES_FILE)

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
                tax_rate.state_unemployment = rates["StateUnemployment"]

                self.tax_rates.append(tax_rate)

    def load_employee_data(self):
        """Reads all employee entries from the appdata directory and serializes them."""
        employee_files = config.EMPLOYEES_DIR.glob('**/*.json')
        for employee_file in employee_files:
            with open(employee_file) as inFile:
                emp = json.load(inFile)

                employee = Employee()
                employee.name = emp["Name"]
                employee.ssn = emp["SSN"]
                employee.pay_rate = emp["PayRate"]
                employee.paid_vacation = emp["PaidVacationHoursPerYear"]
                employee.paid_sick = emp["PaidSickHoursPerYear"]
                employee.paid_holidays = emp["PaidHolidayHoursPerYear"]
                employee.address = emp["Address"]

                self.employees.append(employee)

    def load_timesheet_data(self):
        """Reads all timesheet entries from the appdata directory and serializes them."""

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
                if tax_rate["TaxYear"] == year:
                    return tax_rate
            return None

        # otherwise, return the most recent year
        else:
            current_rates = None
            for tax_rate in self.tax_rates:
                if current_rates is None or current_rates["TaxYear"] < tax_rate["TaxYear"]:
                    current_rates = tax_rate
            return current_rates

    def get_employee_from_name(self, employee_name: str) -> Employee or None:
        """Returns an employee object that matches the provided name."""
        for employee in self.employees:
            if employee.name == employee_name:
                return employee
        return None

    def add_worked_time(self, date: Date, employee_name: str, hours: int or float):
        """Adds a time entry to the provided employee's worked_time list."""
        employee = self.get_employee_from_name(employee_name)
        rates = self.get_tax_rates()

        # check if this date has already been entered
        for time_entry in employee.time_entries:
            if date == time_entry.date:
                raise DuplicateEntryError(f"A time entry for {date} already exists for {employee_name}.")

        time_entry = TimeEntry()
        time_entry.date = date
        time_entry.employee = employee.name
        time_entry.tax_year = rates.year
        time_entry.hours = hours
        time_entry.pay_rate = employee.pay_rate

        employee.time_entries.append(time_entry)
        print(time_entry)

    def get_worked_time_in_range(self, employee_name: str, start_date: Date, end_date: Date) -> list[TimeEntry]:
        """Finds all time entries for the provided employee that match """
        employee = self.get_employee_from_name(employee_name)

        matches = []
        for time_entry in employee.time_entries:
            if start_date <= time_entry.date <= end_date:
                matches.append(time_entry)

        return matches

    def save(self):
        # TODO writes time entries back to disk
        pass
