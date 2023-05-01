
__author__ = 'Sean Kraft'

import os
from pathlib import Path

PROJECT_ROOT = Path(os.path.abspath(__file__)).parent

# project data locations
STUB_DATA_DIR = PROJECT_ROOT / 'stub_data'
STUB_TAX_RATES_FILE = STUB_DATA_DIR / 'stub_tax_rates.json'
STUB_EMPLOYEE_FILE = STUB_DATA_DIR / 'stub_employee.json'

# app data locations
APP_DATA_DIR = Path(os.getenv('APPDATA')) / 'NannyPayrollManager'
TAX_RATES_FILE = APP_DATA_DIR / 'tax_rates.json'
EMPLOYEES_DIR = APP_DATA_DIR / 'Employees'
