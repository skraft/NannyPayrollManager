__author__ = 'Sean Kraft'

from pathlib import Path
from datetime import date as Date
from data_provider import Employee
from data_provider import DataProvider
from data_provider import PayType
from decimal import Decimal

from borb.pdf import Document
from borb.pdf import Page
from borb.pdf.page.page_size import PageSize
from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf import SingleColumnLayout
from borb.pdf import FlexibleColumnWidthTable
from borb.pdf import Paragraph
from borb.pdf import TableCell
from borb.pdf import HexColor
from borb.pdf import PDF


class TimesheetValues:
    def __init__(self):
        self.hours: int = 0
        self.reimbursements: float or int = 0
        self.gross_pay: float or int = 0
        self.medicare_employee: float or int = 0
        self.ss_employee: float or int = 0
        self.paid_fml: float or int = 0
        self.employee_taxes_withheld: float or int = 0
        self.net_pay: float or int = 0
        self.medicare_company: float or int = 0
        self.ss_company: float or int = 0
        self.federal_unemployment: float or int = 0
        self.state_unemployment: float or int = 0
        self.company_tax_contributions: float or int = 0
        self.company_total_costs: float or int = 0

        self.paid_time_off_hours: float or int = 0
        self.paid_holiday_hours: float or int = 0
        self.paid_sick_hours: float or int = 0

    def add_time_entry(self, time_entry):
        self.hours += time_entry.hours
        self.reimbursements += time_entry.reimbursement
        self.gross_pay += time_entry.gross_pay
        self.medicare_employee += time_entry.medicare_employee
        self.ss_employee += time_entry.ss_employee
        self.paid_fml += time_entry.paid_fml
        self.employee_taxes_withheld += time_entry.employee_taxes_withheld
        self.net_pay += time_entry.net_pay
        self.medicare_company += time_entry.medicare_company
        self.ss_company += time_entry.ss_company
        self.federal_unemployment += time_entry.federal_unemployment
        self.state_unemployment += time_entry.state_unemployment
        self.company_tax_contributions += time_entry.company_tax_contributions
        self.company_total_costs += time_entry.company_total_costs

        if time_entry.pay_type is PayType.PAID_TIME_OFF:
            self.paid_time_off_hours += time_entry.hours
        if time_entry.pay_type is PayType.PAID_HOLIDAY:
            self.paid_holiday_hours += time_entry.hours
        if time_entry.pay_type is PayType.PAID_SICK_TIME:
            self.paid_sick_hours += time_entry.hours


class Timesheet:
    def __init__(self, data: DataProvider, employee: Employee, start_date: Date, end_date: Date):
        self.data_provider = data
        self.employee = employee
        self.start_date = start_date
        self.end_date = end_date

        self.timesheet = TimesheetValues()
        self.timesheet_ytd = TimesheetValues()

        self.calculate()

    def calculate(self):
        # tally all year to date time entries
        year_start = Date(self.end_date.year, 1, 1)
        ytd_time_entries = self.data_provider.get_worked_time_in_range(self.employee, year_start, self.end_date)
        for entry in ytd_time_entries:
            entry.tax_rates = self.data_provider.get_tax_rates(year=entry.tax_year)
            self.timesheet_ytd.add_time_entry(entry)

        # tally all time entries in provided time range
        time_entries = self.data_provider.get_worked_time_in_range(self.employee, self.start_date, self.end_date)
        for entry in time_entries:
            entry.tax_rates = self.data_provider.get_tax_rates(year=entry.tax_year)
            self.timesheet.add_time_entry(entry)

        # apply federal unemployment hour cap
        tax_rates = self.data_provider.get_tax_rates(year=self.end_date.year)
        if self.timesheet_ytd.gross_pay > tax_rates.federal_unemployment_hour_cap:
            gross_overage = self.timesheet_ytd.gross_pay - tax_rates.federal_unemployment_hour_cap
            pay_before_overage = self.timesheet.gross_pay - gross_overage
            pay_before_overage = pay_before_overage if pay_before_overage > 0 else 0
            rate = tax_rates.federal_unemployment / 100
            self.timesheet.federal_unemployment = pay_before_overage * rate
            self.timesheet_ytd.federal_unemployment = tax_rates.federal_unemployment_hour_cap * rate

    def to_pdf(self, file_path: Path):
        f_size = Decimal(8)
        f_bold = "Helvetica-bold"

        # build doc and layout
        doc = Document()
        page = Page(width=PageSize.A4_LANDSCAPE.value[0], height=PageSize.A4_LANDSCAPE.value[1])
        doc.add_page(page)
        layout = SingleColumnLayout(page)

        # add timesheet table
        table = FlexibleColumnWidthTable(number_of_rows=25, number_of_columns=7)

        # row 1
        text = Paragraph("Employee Earnings", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=HexColor("6AA84F"), col_span=7))

        # row 2
        text = Paragraph("Description", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100)))
        text = Paragraph("Rate", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100)))
        text = Paragraph("Hours", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(100)))

        # row 3
        table.add(TableCell(Paragraph("Gross Earnings", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(f"${self.employee.pay_rate:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(str(self.timesheet.hours), font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(f"${self.timesheet.gross_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(f"${self.timesheet_ytd.gross_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))

        # row 4
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        table.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))

        layout.add(table)

        with open(file_path, "wb") as pdf_file:
            PDF.dumps(pdf_file, doc)
        print(f"{file_path} saved.")

    def print_timesheet(self):
        print('--THIS PAY PERIOD--')
        print(f'Hours: {self.timesheet.hours}')
        print(f'Total Gross Pay: ${round(self.timesheet.gross_pay, 2)}')
        print('Employee Taxes:')
        print(f' - Medicare Employee: ${round(self.timesheet.medicare_employee, 2)}')
        print(f' - Social Security Employee: ${round(self.timesheet.ss_employee, 2)}')
        print(f' - WA Paid Family and Medical Leave: ${round(self.timesheet.paid_fml, 2)}')
        print(f' - Total Taxes Withheld: ${round(self.timesheet.employee_taxes_withheld, 2)}')
        print(f'Milage and General Reimbursements: ${round(self.timesheet.reimbursements, 2)}')
        print(f'Net Pay: ${round(self.timesheet.net_pay, 2)}')
        print('Employer Taxes:')
        print(f' - Medicare Employer: ${round(self.timesheet.medicare_company, 2)}')
        print(f' - Social Security Employer: ${round(self.timesheet.ss_company, 2)}')
        print(f' - Federal Unemployment: ${round(self.timesheet.federal_unemployment, 2)}')
        print(f' - WA State Unemployment: ${round(self.timesheet.state_unemployment, 2)}')
        print(f' - Employer Tax Contributions: ${round(self.timesheet.company_tax_contributions, 2)}')
        print(f'Employer Total Costs: ${round(self.timesheet.company_total_costs, 2)}')

        print('\n--YEAR TO DATE--')
        print(f'Hours: {self.timesheet_ytd.hours}')
        print(f'Total Gross Pay: ${round(self.timesheet_ytd.gross_pay, 2)}')
        print('Employee Taxes:')
        print(f' - Medicare Employee: ${round(self.timesheet_ytd.medicare_employee, 2)}')
        print(f' - Social Security Employee: ${round(self.timesheet_ytd.ss_employee, 2)}')
        print(f' - WA Paid Family and Medical Leave: ${round(self.timesheet_ytd.paid_fml, 2)}')
        print(f' - Total Taxes Withheld: ${round(self.timesheet_ytd.employee_taxes_withheld, 2)}')
        print(f'Milage and General Reimbursements: ${round(self.timesheet_ytd.reimbursements, 2)}')
        print(f'Net Pay: ${round(self.timesheet_ytd.net_pay, 2)}')
        print('Employer Taxes:')
        print(f' - Medicare Employer: ${round(self.timesheet_ytd.medicare_company, 2)}')
        print(f' - Social Security Employer: ${round(self.timesheet_ytd.ss_company, 2)}')
        print(f' - Federal Unemployment: ${round(self.timesheet_ytd.federal_unemployment, 2)}')
        print(f' - WA State Unemployment: ${round(self.timesheet_ytd.state_unemployment, 2)}')
        print(f' - Employer Tax Contributions: ${round(self.timesheet_ytd.company_tax_contributions, 2)}')
        print(f'Employer Total Costs: ${round(self.timesheet_ytd.company_total_costs, 2)}')

        print('\n--PAID TIME OFF--')
        print(f'Paid Time Off Used To-Date (hours): {self.timesheet_ytd.paid_time_off_hours}')
        print(f'Paid Time Off Remaining (hours): {self.employee.paid_vacation - self.timesheet_ytd.paid_time_off_hours}')
        print(f'Paid Holidays Used To-Date (hours): {self.timesheet_ytd.paid_holiday_hours}')
        print(f'Paid Holiday Remaining (hours): {self.employee.paid_holidays - self.timesheet_ytd.paid_holiday_hours}')
        print(f'Paid Sick Time Used To-Date (hours): {self.timesheet_ytd.paid_sick_hours}')
        print(f'Paid Sick Time Remaining (hours): {self.employee.paid_sick - self.timesheet_ytd.paid_sick_hours}')


