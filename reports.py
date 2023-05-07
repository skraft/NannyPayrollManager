__author__ = 'Sean Kraft'

from datetime import date as Date
import data_provider


class Reports:
    def __init__(self, data_provider_instance: data_provider.DataProvider):
        self.data_provider = data_provider_instance

    def timesheet(self, employee_name: str, start_date: Date, end_date: Date):
        # TODO what happens if a timesheet is requested that spans more than one year?
        # TODO handle PTO, vacation, and sick time
        # TODO federal unemployment needs the $7000 limit implemented

        # build all output variables
        hours = 0
        reimbursements = 0
        gross_pay = 0
        medicare_employee = 0
        ss_employee = 0
        paid_fml = 0
        employee_taxes_withheld = 0
        net_pay = 0
        medicare_company = 0
        ss_company = 0
        federal_unemployment = 0
        state_unemployment = 0
        company_tax_contributions = 0
        company_total_costs = 0

        ytd_hours = 0
        ytd_reimbursements = 0
        ytd_gross_pay = 0
        ytd_medicare_employee = 0
        ytd_ss_employee = 0
        ytd_paid_fml = 0
        ytd_employee_taxes_withheld = 0
        ytd_net_pay = 0
        ytd_medicare_company = 0
        ytd_ss_company = 0
        ytd_federal_unemployment = 0
        ytd_state_unemployment = 0
        ytd_company_tax_contributions = 0
        ytd_company_total_costs = 0

        # year to date data
        year_start = Date(end_date.year, 1, 1)
        ytd_time_entries = self.data_provider.get_worked_time_in_range(employee_name, year_start, end_date)
        for entry in ytd_time_entries:
            # populate tax rate data so tax calculates can be made
            entry.tax_rates = self.data_provider.get_tax_rates(year=entry.tax_year)

            ytd_hours += entry.hours
            ytd_reimbursements += entry.reimbursement
            ytd_gross_pay += entry.gross_pay
            ytd_medicare_employee += entry.medicare_employee
            ytd_ss_employee += entry.ss_employee
            ytd_paid_fml += entry.paid_fml
            ytd_employee_taxes_withheld += entry.employee_taxes_withheld
            ytd_net_pay += entry.net_pay
            ytd_medicare_company += entry.medicare_company
            ytd_ss_company += entry.ss_company
            ytd_federal_unemployment += entry.federal_unemployment
            ytd_state_unemployment += entry.state_unemployment
            ytd_company_tax_contributions += entry.company_tax_contributions
            ytd_company_total_costs += entry.company_total_costs

        # apply federal unemployment hour cap to year-to-date hours
        tax_rates = self.data_provider.get_tax_rates(year=end_date.year)
        if ytd_gross_pay > tax_rates.federal_unemployment_hour_cap:
            ytd_federal_unemployment = tax_rates.federal_unemployment_hour_cap * (tax_rates.federal_unemployment / 100)

        # timesheet range data
        time_entries = self.data_provider.get_worked_time_in_range(employee_name, start_date, end_date)
        for entry in time_entries:
            # populate tax rate data so tax calculates can be made
            entry.tax_rates = self.data_provider.get_tax_rates(year=entry.tax_year)

            hours += entry.hours
            reimbursements += entry.reimbursement
            gross_pay += entry.gross_pay
            medicare_employee += entry.medicare_employee
            ss_employee += entry.ss_employee
            paid_fml += entry.paid_fml
            employee_taxes_withheld += entry.employee_taxes_withheld
            net_pay += entry.net_pay
            medicare_company += entry.medicare_company
            ss_company += entry.ss_company
            federal_unemployment += entry.federal_unemployment
            state_unemployment += entry.state_unemployment
            company_tax_contributions += entry.company_tax_contributions
            company_total_costs += entry.company_total_costs

        print('--THIS PAY PERIOD--')
        print(f'Hours: {hours}')
        print(f'Milage and General Reimbursements: ${round(reimbursements, 2)}')
        print(f'Total Gross Pay: ${round(gross_pay, 2)}')
        print('Employee Taxes:')
        print(f' - Medicare Employee: ${round(medicare_employee, 2)}')
        print(f' - Social Security Employee: ${round(ss_employee, 2)}')
        print(f' - WA Paid Family and Medical Leave: ${round(paid_fml, 2)}')
        print(f' - Total Taxes Withheld: ${round(employee_taxes_withheld, 2)}')
        print(f'Net Pay: ${round(net_pay, 2)}')
        print('Employer Taxes:')
        print(f' - Medicare Employer: ${round(medicare_company, 2)}')
        print(f' - Social Security Employer: ${round(ss_company, 2)}')
        print(f' - Federal Unemployment: ${round(federal_unemployment, 2)}')
        print(f' - WA State Unemployment: ${round(state_unemployment, 2)}')
        print(f' - Employer Tax Contributions: ${round(company_tax_contributions, 2)}')
        print(f'Employer Total Costs: ${round(company_total_costs, 2)}')
        print('\n--YEAR TO DATE--')
        print(f'Hours: {ytd_hours}')
        print(f'Milage and General Reimbursements: ${round(ytd_reimbursements, 2)}')
        print(f'Total Gross Pay: ${round(ytd_gross_pay, 2)}')
        print('Employee Taxes:')
        print(f' - Medicare Employee: ${round(ytd_medicare_employee, 2)}')
        print(f' - Social Security Employee: ${round(ytd_ss_employee, 2)}')
        print(f' - WA Paid Family and Medical Leave: ${round(ytd_paid_fml, 2)}')
        print(f' - Total Taxes Withheld: ${round(ytd_employee_taxes_withheld, 2)}')
        print(f'Net Pay: ${round(ytd_net_pay, 2)}')
        print('Employer Taxes:')
        print(f' - Medicare Employer: ${round(ytd_medicare_company, 2)}')
        print(f' - Social Security Employer: ${round(ytd_ss_company, 2)}')
        print(f' - Federal Unemployment: ${round(ytd_federal_unemployment, 2)}')
        print(f' - WA State Unemployment: ${round(ytd_state_unemployment, 2)}')
        print(f' - Employer Tax Contributions: ${round(ytd_company_tax_contributions, 2)}')
        print(f'Employer Total Costs: ${round(ytd_company_total_costs, 2)}')

