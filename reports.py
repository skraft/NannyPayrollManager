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


class MyParagraph(Paragraph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vertical_alignment = Alignment.MIDDLE
        self.horizontal_alignment = Alignment.RIGHT


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
        self.check_amount: float or int = 0
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
        self.check_amount += time_entry.check_amount
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
        f_size_l = Decimal(10)
        f_bold = "Helvetica-bold"
        color_bdr = HexColor("6AA84F")
        color_red = HexColor("ED1C24")
        color_lt_green = HexColor("D9EAD3")

        # build doc and layout
        doc = Document()
        page = Page(width=PageSize.A4_LANDSCAPE.value[0], height=PageSize.A4_LANDSCAPE.value[1])
        doc.add_page(page)
        layout = SingleColumnLayout(page)

        # add timesheet table
        table = FlexibleColumnWidthTable(number_of_rows=24, number_of_columns=7)

        # row 1: Earnings Title
        text = Paragraph("Employee Earnings", font=f_bold, font_size=f_size_l)
        table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=7))

        # row 2: Earnings: Headers
        text = Paragraph("Description", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        text = Paragraph("Rate", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        text = Paragraph("Hours", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))

        # row 3: Earnings: Gross Earnings
        table.add(TableCell(Paragraph("Gross Pay", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(f"${self.employee.pay_rate:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(str(self.timesheet.hours), font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(f"${self.timesheet.gross_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(f"${self.timesheet_ytd.gross_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))

        # row 4: BLANK
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 5: Tax: Titles
        text = Paragraph("Employee Taxes Withheld", font=f_bold, font_size=f_size_l)
        table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Employer Taxes", font=f_bold, font_size=f_size_l)
        table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))

        # row 6: Tax: Headers
        text = Paragraph("Employee Tax", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Household Employer Tax", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))

        # row 7: Tax: Medicare
        table.add(TableCell(Paragraph("Medicare", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.medicare_employee:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.medicare_employee:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph("Medicare", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.medicare_company:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.medicare_company:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 8: Tax: Social Security
        table.add(TableCell(Paragraph("Social Security", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.ss_employee:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.ss_employee:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph("Social Security", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.ss_company:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.ss_company:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 9: Tax: Family Medical Leave and Federal Unemployment
        table.add(TableCell(Paragraph("WA Family Medical Leave", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.paid_fml:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.paid_fml:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph("Federal Unemployment", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.federal_unemployment:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.federal_unemployment:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 10: Tax: State Unemployment
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph("WA State Unemployment", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.state_unemployment:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.state_unemployment:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 11: BLANK
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 12: Summary: Title
        text = Paragraph("Summary", font=f_bold, font_size=f_size_l)
        table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=7))

        # row 13: Summary: Headers
        text = Paragraph("Description", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))

        # row 14: Summary: Gross Earnings
        table.add(TableCell(Paragraph("Gross Pay", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.gross_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.gross_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 15: Summary: Employee Taxes Withheld
        table.add(TableCell(Paragraph("Employee Taxes Withheld", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.employee_taxes_withheld:.2f}", font_size=f_size, font_color=color_red, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.employee_taxes_withheld:.2f}", font_size=f_size, font_color=color_red, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 16: Summary: Net Pay
        table.add(TableCell(Paragraph("Net Pay", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.net_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.net_pay:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 17: Summary: Reimbursements
        table.add(TableCell(Paragraph("Reimbursements", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.reimbursements:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.reimbursements:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 18: Summary: Check Amount
        table.add(TableCell(Paragraph("Check Amount", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.check_amount:.2f}", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), background_color=color_lt_green))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.check_amount:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 19: BLANK
        table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 20: Time Off Benefits: Title
        text = Paragraph("Time Off Benefits", font=f_bold, font_size=f_size_l)
        table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=7))

        # row 21: Time Off Benefits: Headers
        text = Paragraph("Description", font=f_bold, font_size=f_size)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Used Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Used Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Available", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))

        # row 22: Time Off Benefits: Paid Time Off
        table.add(TableCell(Paragraph("Paid Time Off (Hours)", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet.paid_time_off_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet_ytd.paid_time_off_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.employee.paid_vacation - self.timesheet_ytd.paid_time_off_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 23: Time Off Benefits: Sick Time
        table.add(TableCell(Paragraph("Paid Sick Time (Hours)", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet.paid_sick_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet_ytd.paid_sick_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.employee.paid_sick - self.timesheet_ytd.paid_sick_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

        # row 24: Time Off Benefits: Paid Holidays
        table.add(TableCell(Paragraph("Paid Holidays (Hours)", font_size=f_size), border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet.paid_holiday_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet_ytd.paid_holiday_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))
        table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.employee.paid_holidays - self.timesheet_ytd.paid_holiday_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        table.add(TableCell(text, border_width=Decimal(0)))

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


