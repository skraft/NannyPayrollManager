
__author__ = 'Sean Kraft'

from pathlib import Path
import config
import shutil


class DataProvider:
    def __init__(self):

        self.first_run = False

        # if required appdata folders don't exist, create them
        self.init_appdata_dir()

        # load all tax rate data
        self.load_tax_rate_data()

        # load all employee data
        self.load_employee_data()

        # load all timesheet data
        self.load_timesheet_data()

    def init_appdata_dir(self):
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
        pass

    def load_employee_data(self):
        pass

    def load_timesheet_data(self):
        pass

    def make_new_employee(self, name):
        employee_name = name.replace(" ", "")
        employee_dir = config.EMPLOYEES_DIR / employee_name
        if employee_dir.exists():
            raise FileExistsError(f'A directory named {employee_name} already exists.')

        employee_dir.mkdir(parents=True)
        shutil.copy(config.STUB_EMPLOYEE_FILE, employee_dir / (employee_name + '.json'))

        self.load_employee_data()
