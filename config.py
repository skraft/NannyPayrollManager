
__author__ = 'Sean Kraft'

import os
from pathlib import Path

PROJECT_ROOT = Path(os.path.abspath(__file__)).parent

# project data locations
STUB_DATA_DIR = PROJECT_ROOT / 'stub_data'
STUB_TAX_RATES_FILE = STUB_DATA_DIR / 'stub_tax_rates.json'
STUB_EMPLOYER_FILE = STUB_DATA_DIR / 'stub_employer.json'
STUB_EMPLOYEE_FILE = STUB_DATA_DIR / 'stub_employee.json'

# app data locations
APP_DATA_DIR = Path(os.getenv('APPDATA')) / 'NannyPayrollManager'
TAX_RATES_FILE = APP_DATA_DIR / 'tax_rates.json'
EMPLOYER_FILE = APP_DATA_DIR / 'employer.json'
PAID_HOLIDAYS_FILE = APP_DATA_DIR / 'paid_holidays.json'
EMPLOYEES_DIR = APP_DATA_DIR / 'Employees'

# default timesheet location
TIMESHEET_DIR = Path.home() / "Downloads"

# washington state EAMS standard occupational code
EAMS_OCCUPATIONAL_CODE = "399011"  # Childcare Workers