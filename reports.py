__author__ = 'Sean Kraft'

from pathlib import Path
from datetime import date as Date
from datetime import timedelta
import csv
import math

import config
from data_provider import TimeEntry
from data_provider import Employee
from data_provider import DataProvider
from data_provider import PayType
from data_provider import TaxRates
from data_provider import W4FilingStatus
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
        self.wa_paid_fml_employee: float or int = 0
        self.wa_cares: float or int = 0
        self.employee_taxes_withheld: float or int = 0
        self.net_pay: float or int = 0
        self.check_amount: float or int = 0
        self.medicare_company: float or int = 0
        self.ss_company: float or int = 0
        self.wa_paid_fml_company: float or int = 0
        self.federal_unemployment: float or int = 0
        self.state_unemployment: float or int = 0
        self.company_tax_contributions: float or int = 0
        self.company_total_costs: float or int = 0

        self.federal_withholding: float or int = 0

        self.paid_time_off_hours: float or int = 0
        self.paid_holiday_hours: float or int = 0
        self.paid_sick_hours: float or int = 0

    def add_time_entry(self, time_entry: TimeEntry):
        self.hours += time_entry.hours
        self.reimbursements += time_entry.reimbursement
        self.gross_pay += time_entry.gross_pay
        self.medicare_employee += time_entry.medicare_employee
        self.ss_employee += time_entry.ss_employee
        self.wa_paid_fml_employee += time_entry.wa_paid_fml_employee
        self.wa_cares += time_entry.wa_cares
        self.employee_taxes_withheld += time_entry.employee_taxes_withheld
        self.net_pay += time_entry.net_pay
        self.check_amount += time_entry.check_amount
        self.medicare_company += time_entry.medicare_company
        self.ss_company += time_entry.ss_company
        self.wa_paid_fml_company += time_entry.wa_paid_fml_company
        self.federal_unemployment += time_entry.federal_unemployment
        self.state_unemployment += time_entry.state_unemployment
        self.company_tax_contributions += time_entry.company_tax_contributions
        self.company_total_costs += time_entry.company_total_costs

        if time_entry.federal_withholding:
            self.federal_withholding += time_entry.federal_withholding

        if time_entry.pay_type is PayType.PAID_TIME_OFF:
            self.paid_time_off_hours += time_entry.hours
        if time_entry.pay_type is PayType.PAID_HOLIDAY:
            self.paid_holiday_hours += time_entry.hours
        if time_entry.pay_type is PayType.PAID_SICK_TIME:
            self.paid_sick_hours += time_entry.hours


class QuarterlyReportValues:
    def __init__(self):
        self.employee: Employee or None = None
        self.hours: float or int = 0
        self.gross_pay: float or int = 0

    def __repr__(self):
        return f"QuarterlyReportValues(employee={self.employee}, hours={self.hours}, gross_pay={self.gross_pay})"

    def add_time_entry(self, time_entry: TimeEntry):
        self.hours += time_entry.hours
        self.gross_pay += time_entry.gross_pay


def get_first_payday_of_year(year: int, payroll_day_of_week: int = 4):
    """Returns the first payroll date of the provided year."""
    year_start = Date(year, 1, 1)
    first_payday = year_start - timedelta(days=(Date.weekday(year_start) - payroll_day_of_week))
    if first_payday.year < year_start.year:
        first_payday += timedelta(weeks=1)
    return first_payday


def calculate_federal_withholding(gross_pay: float, employee: Employee, tax_rates: TaxRates) -> float:
    """Calculates the federal withholding for a SINGLE PAY PERIOD (if the employee provided a W4).
    this procedure comes from Pub 15-T, Worksheet 1A. This function assumes a 2020 or later W4 form."""
    if employee.w4 is None:
        return 0

    # step 1
    line_1c = gross_pay * employee.w4.pay_periods_per_year
    line_1e = line_1c + employee.w4.line_4A
    if employee.w4.line_2C:
        line_1g = 0
    else:
        married_rate = tax_rates.federal_withholding["Worksheet1A_1G_Married"]
        not_married_rate = tax_rates.federal_withholding["Worksheet1A_1G_NotMarried"]
        line_1g = married_rate if employee.w4.line_1C is W4FilingStatus.MARRIED else not_married_rate
    line_1h = line_1g + employee.w4.line_4B
    adjusted_annual_wage_amount = max(0, (line_1e - line_1h))  # negative values should be 0

    # step 2
    withholding_table = tax_rates.get_federal_withholding_table(employee)
    withholding_row = None
    for row in withholding_table:
        if row["A"] <= adjusted_annual_wage_amount < row["B"]:
            withholding_row = row
            break
    line_2e = adjusted_annual_wage_amount - withholding_row["A"]
    line_2f = line_2e * (withholding_row["D"] / 100)
    line_2g = withholding_row["C"] + line_2f
    tentative_withholding_amount = line_2g / employee.w4.pay_periods_per_year

    # step 3
    line_3b = employee.w4.line_3 / employee.w4.pay_periods_per_year
    line_3c = max(0, (tentative_withholding_amount - line_3b))

    # step 4
    final_withholding = line_3c + employee.w4.line_4C
    return round(final_withholding, 2)


class Timesheet:
    def __init__(self, data: DataProvider, employee: Employee, start_date: Date, end_date: Date):
        self.data_provider = data
        self.employee = employee
        self.employer = self.data_provider.employer
        self.start_date = start_date
        self.end_date = end_date

        self.federal_withholding_amount = 0

        self.timesheet = TimesheetValues()
        self.timesheet_ytd = TimesheetValues()

        self.calculate()

    def calculate(self):
        tax_rates = self.data_provider.get_tax_rates(year=self.end_date.year)
        time_entries = self.data_provider.get_worked_time_in_range(self.employee, self.start_date, self.end_date)

        if not time_entries:
            print('WARNING: No time entries found in the provided date range.')

        # timesheets must end on the employer payroll day of week
        if Date.weekday(self.end_date) != self.employer.payroll_day:
            raise ValueError(f"Timesheets must end on {self.employer.payroll_day_name} as defined in employer.json.")

        # calculate federal withholding for this pay period (unless it's already been calculated)
        timesheet_range = self.end_date - self.start_date
        if time_entries:
            if timesheet_range > timedelta(days=6) or timesheet_range < timedelta(days=4):
                print("WARNING: Unable to calculate federal withholding for non-weekly timesheets.")
            else:
                last_entry = time_entries[-1]
                if last_entry.federal_withholding is None:
                    gross_pay = sum([entry.gross_pay for entry in time_entries])
                    last_entry.federal_withholding = calculate_federal_withholding(gross_pay, self.employee, tax_rates)
                    self.employee._time_entries_dirty = True
                    self.data_provider.save()
                    print(f"Added ${last_entry.federal_withholding:.2f} of Federal Withholding to {last_entry.date}.")

        # tally all year to date time entries
        year_start = get_first_payday_of_year(self.end_date.year, self.employer.payroll_day) - timedelta(days=6)
        ytd_time_entries = self.data_provider.get_worked_time_in_range(self.employee, year_start, self.end_date)
        for entry in ytd_time_entries:
            entry.tax_rates = self.data_provider.get_tax_rates(year=entry.tax_year)
            self.timesheet_ytd.add_time_entry(entry)

        # tally all time entries in provided time range
        for entry in time_entries:
            entry.tax_rates = self.data_provider.get_tax_rates(year=entry.tax_year)
            self.timesheet.add_time_entry(entry)

        # apply federal unemployment hour cap
        if self.timesheet_ytd.gross_pay > tax_rates.federal_unemployment_taxable_max:
            gross_overage = self.timesheet_ytd.gross_pay - tax_rates.federal_unemployment_taxable_max
            pay_before_overage = max(0, (self.timesheet.gross_pay - gross_overage))
            self.timesheet.federal_unemployment = pay_before_overage * tax_rates.federal_unemployment
            self.timesheet_ytd.federal_unemployment = tax_rates.federal_unemployment_taxable_max * tax_rates.federal_unemployment

        # apply social security taxable wages cap to social security and wa family medical leave withholdings
        if self.timesheet_ytd.gross_pay > tax_rates.ss_taxable_max:
            gross_overage = self.timesheet_ytd.gross_pay - tax_rates.ss_taxable_max
            pay_before_overage = max(0, (self.timesheet.gross_pay - gross_overage))
            self.timesheet.ss_employee = pay_before_overage * tax_rates.ss_employee
            self.timesheet.ss_company = pay_before_overage * tax_rates.ss_company
            self.timesheet_ytd.ss_employee = tax_rates.ss_taxable_max * tax_rates.ss_employee
            self.timesheet_ytd.ss_company = tax_rates.ss_taxable_max * tax_rates.ss_company
            self.timesheet.wa_paid_fml_employee = pay_before_overage * tax_rates.wa_paid_fml_employee
            self.timesheet.wa_paid_fml_company = pay_before_overage * tax_rates.wa_paid_fml_company
            self.timesheet_ytd.wa_paid_fml_employee = tax_rates.ss_taxable_max * tax_rates.wa_paid_fml_employee
            self.timesheet_ytd.wa_paid_fml_company = tax_rates.ss_taxable_max * tax_rates.wa_paid_fml_company

        # subtract federal withholding from net pay and check amount
        self.timesheet.employee_taxes_withheld += self.timesheet.federal_withholding
        self.timesheet.net_pay -= self.timesheet.federal_withholding
        self.timesheet.check_amount -= self.timesheet.federal_withholding
        self.timesheet_ytd.employee_taxes_withheld += self.timesheet_ytd.federal_withholding
        self.timesheet_ytd.net_pay -= self.timesheet_ytd.federal_withholding
        self.timesheet_ytd.check_amount -= self.timesheet_ytd.federal_withholding

    def to_pdf(self, file_path: Path):
        f_size = Decimal(8)
        f_size_l = Decimal(10)
        f_bold = "Helvetica-bold"
        color_bdr = HexColor("6AA84F")
        color_red = HexColor("ED1C24")
        color_lt_green = HexColor("D9EAD3")

        start_date = self.start_date.strftime("%b %d, %Y")
        end_date = self.end_date.strftime("%b %d, %Y")

        # build doc and layout
        doc = Document()
        page = Page(width=PageSize.A4_LANDSCAPE.value[0], height=PageSize.A4_LANDSCAPE.value[1])
        doc.add_page(page)
        layout = SingleColumnLayout(page)
        layout._vertical_margin_top = 50
        layout._vertical_margin_bottom = 10

        layout.add(Paragraph(f"Earnings Statement : {end_date}", font=f_bold, font_size=Decimal(16)))

        # add timesheet table
        ts_table = FlexibleColumnWidthTable(number_of_rows=28, number_of_columns=7)

        # # row 1: Address Titles
        text = Paragraph("Employee", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Employer", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))

        # row 2: Name + Address
        text = Paragraph(f"{self.employee.name}\n{self.employee.address_multiline}", font_size=f_size, respect_newlines_in_text=True)
        ts_table.add(TableCell(text, border_width=Decimal(0), col_span=3, padding_top=Decimal(3), padding_bottom=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        text = Paragraph(f"{self.data_provider.employer.name}\n{self.data_provider.employer.address_multiline}", font_size=f_size, respect_newlines_in_text=True)
        ts_table.add(TableCell(text, border_width=Decimal(0), col_span=3, padding_top=Decimal(3), padding_bottom=Decimal(3)))

        # row 3: BLANK
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 4: Earnings Title
        text = Paragraph("Employee Earnings", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=7))

        # row 5: Earnings: Headers
        text = Paragraph("Pay Period", font=f_bold, font_size=f_size)
        ts_table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(120), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        text = Paragraph("Rate", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        text = Paragraph("Hours", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(30)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), preferred_width=Decimal(100), padding_top=Decimal(3)))

        # row 6: Earnings: Gross Earnings
        ts_table.add(TableCell(Paragraph(f"{start_date} - {end_date}", font_size=f_size), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(f"${self.employee.pay_rate:.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(str(self.timesheet.hours), font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(f"${self.timesheet.gross_pay:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(f"${self.timesheet_ytd.gross_pay:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))

        # row 7: BLANK
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 8: Tax: Titles
        text = Paragraph("Employee Taxes Withheld", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Employer Taxes", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))

        # row 9: Tax: Headers
        text = Paragraph("Employee Tax", font=f_bold, font_size=f_size)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Household Employer Tax", font=f_bold, font_size=f_size)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))

        # row 10: Tax: Medicare
        ts_table.add(TableCell(Paragraph("Medicare", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.medicare_employee:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.medicare_employee:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph("Medicare", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.medicare_company:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.medicare_company:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 11: Tax: Social Security
        ts_table.add(TableCell(Paragraph("Social Security", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.ss_employee:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.ss_employee:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph("Social Security", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.ss_company:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.ss_company:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 12: Tax: WA Paid Family Medical Leave
        ts_table.add(TableCell(Paragraph("WA Family Medical Leave", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.wa_paid_fml_employee:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.wa_paid_fml_employee:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph("WA Family Medical Leave", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.wa_paid_fml_company:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.wa_paid_fml_company:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 13: Tax: WA Cares and Federal Unemployment
        ts_table.add(TableCell(Paragraph("WA Cares", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.wa_cares:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.wa_cares:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph("Federal Unemployment", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.federal_unemployment:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.federal_unemployment:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 14: Tax: Federal Withholding and State Unemployment
        ts_table.add(TableCell(Paragraph("Federal Withholding", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(F"${self.timesheet.federal_withholding:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(F"${self.timesheet_ytd.federal_withholding:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph("WA State Unemployment", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.state_unemployment:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.state_unemployment:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 15: BLANK
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 16: Time Off Benefits: Title
        text = Paragraph("Time Off Benefits", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=7))

        # row 17: Time Off Benefits: Headers
        text = Paragraph("Description", font=f_bold, font_size=f_size)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Used Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Used Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph("Available", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))

        # row 18: Time Off Benefits: Paid Time Off
        ts_table.add(TableCell(Paragraph("Paid Time Off (Hours)", font_size=f_size), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet.paid_time_off_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet_ytd.paid_time_off_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.employee.paid_vacation - self.timesheet_ytd.paid_time_off_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 19: Time Off Benefits: Sick Time
        ts_table.add(TableCell(Paragraph("Paid Sick Time (Hours)", font_size=f_size), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet.paid_sick_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet_ytd.paid_sick_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.employee.paid_sick - self.timesheet_ytd.paid_sick_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 20: Time Off Benefits: Paid Holidays
        ts_table.add(TableCell(Paragraph("Paid Holidays (Hours)", font_size=f_size), border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet.paid_holiday_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.timesheet_ytd.paid_holiday_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0)))
        text = Paragraph(f"{self.employee.paid_holidays - self.timesheet_ytd.paid_holiday_hours}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 21: BLANK
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=7))

        # row 22: Summary: Title
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        text = Paragraph("Summary", font=f_bold, font_size=f_size_l)
        ts_table.add(TableCell(text, border_top=False, border_right=False, border_left=False, border_bottom=True, border_color=color_bdr, col_span=3))

        # row 23: Summary: Headers
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        text = Paragraph("Description", font=f_bold, font_size=f_size)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3), padding_bottom=Decimal(3)))
        text = Paragraph("Current Pay Period", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))
        text = Paragraph("Year To Date", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), padding_top=Decimal(3)))

        # row 24: Summary: Gross Earnings
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        ts_table.add(TableCell(Paragraph("Gross Pay", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.gross_pay:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.gross_pay:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 25: Summary: Employee Taxes Withheld
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        ts_table.add(TableCell(Paragraph("Employee Taxes Withheld", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.employee_taxes_withheld:,.2f}", font_size=f_size, font_color=color_red, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.employee_taxes_withheld:,.2f}", font_size=f_size, font_color=color_red, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 26: Summary: Net Pay
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        ts_table.add(TableCell(Paragraph("Net Pay", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.net_pay:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.net_pay:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 27: Summary: Reimbursements
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        ts_table.add(TableCell(Paragraph("Reimbursements", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.reimbursements:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet_ytd.reimbursements:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        # row 28: Summary: Check Amount
        ts_table.add(TableCell(Paragraph(""), border_width=Decimal(0), col_span=4))
        ts_table.add(TableCell(Paragraph("Check Amount", font_size=f_size), border_width=Decimal(0)))
        text = Paragraph(f"${self.timesheet.check_amount:,.2f}", font=f_bold, font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0), background_color=color_lt_green))
        text = Paragraph(f"${self.timesheet_ytd.check_amount:,.2f}", font_size=f_size, horizontal_alignment=Alignment.RIGHT)
        ts_table.add(TableCell(text, border_width=Decimal(0)))

        layout.add(ts_table)

        with open(file_path, "wb") as pdf_file:
            PDF.dumps(pdf_file, doc)
        print(f"{file_path} saved.")

    def to_console(self):
        print("--THIS PAY PERIOD--")
        print(f"Hours: {self.timesheet.hours}")
        print(f'Total Gross Pay: ${self.timesheet.gross_pay:,.2f}')
        print('Employee Taxes:')
        print(f' - Medicare Employee: ${self.timesheet.medicare_employee:,.2f}')
        print(f' - Social Security Employee: ${self.timesheet.ss_employee:,.2f}')
        print(f' - WA Paid Family and Medical Leave: ${self.timesheet.wa_paid_fml_employee:,.2f}')
        print(f' - WA Cares: ${self.timesheet.wa_cares:,.2f}')
        print(f' - Federal Withholding: ${self.timesheet.federal_withholding:,.2f}')
        print(f' - Total Taxes Withheld: ${self.timesheet.employee_taxes_withheld:,.2f}')
        print(f'Net Pay: ${self.timesheet.net_pay:,.2f}')
        print(f'Milage and General Reimbursements: ${self.timesheet.reimbursements:,.2f}')
        print(f'Check Amount: ${self.timesheet.check_amount:,.2f}')
        print('Employer Taxes:')
        print(f' - Medicare Employer: ${self.timesheet.medicare_company:,.2f}')
        print(f' - Social Security Employer: ${self.timesheet.ss_company:,.2f}')
        print(f' - WA Paid Family and Medical Leave: ${self.timesheet.wa_paid_fml_company:,.2f}')
        print(f' - Federal Unemployment: ${self.timesheet.federal_unemployment:,.2f}')
        print(f' - WA State Unemployment: ${self.timesheet.state_unemployment:,.2f}')
        print(f' - Employer Tax Contributions: ${self.timesheet.company_tax_contributions:,.2f}')
        print(f'Employer Total Costs: ${self.timesheet.company_total_costs:,.2f}')

        print('\n--YEAR TO DATE--')
        print(f'Hours: {self.timesheet_ytd.hours}')
        print(f'Total Gross Pay: ${self.timesheet_ytd.gross_pay:,.2f}')
        print('Employee Taxes:')
        print(f' - Medicare Employee: ${self.timesheet_ytd.medicare_employee:,.2f}')
        print(f' - Social Security Employee: ${self.timesheet_ytd.ss_employee:,.2f}')
        print(f' - WA Paid Family and Medical Leave: ${self.timesheet_ytd.wa_paid_fml_employee:,.2f}')
        print(f' - WA Cares: ${self.timesheet_ytd.wa_cares:,.2f}')
        print(f' - Federal Withholding: ${self.timesheet_ytd.federal_withholding:,.2f}')
        print(f' - Total Taxes Withheld: ${self.timesheet_ytd.employee_taxes_withheld:,.2f}')
        print(f'Net Pay: ${self.timesheet_ytd.net_pay:,.2f}')
        print(f'Milage and General Reimbursements: ${self.timesheet_ytd.reimbursements:,.2f}')
        print(f'Check Amount: ${self.timesheet_ytd.check_amount:,.2f}')
        print('Employer Taxes:')
        print(f' - Medicare Employer: ${self.timesheet_ytd.medicare_company:,.2f}')
        print(f' - Social Security Employer: ${self.timesheet_ytd.ss_company:,.2f}')
        print(f' - WA Paid Family and Medical Leave: ${self.timesheet_ytd.wa_paid_fml_company:,.2f}')
        print(f' - Federal Unemployment: ${self.timesheet_ytd.federal_unemployment:,.2f}')
        print(f' - WA State Unemployment: ${self.timesheet_ytd.state_unemployment:,.2f}')
        print(f' - Employer Tax Contributions: ${self.timesheet_ytd.company_tax_contributions:,.2f}')
        print(f'Employer Total Costs: ${self.timesheet_ytd.company_total_costs:,.2f}')

        print('\n--PAID TIME OFF--')
        print(f'Paid Time Off Used To-Date (hours): {self.timesheet_ytd.paid_time_off_hours}')
        print(f'Paid Time Off Remaining (hours): {self.employee.paid_vacation - self.timesheet_ytd.paid_time_off_hours}')
        print(f'Paid Holidays Used To-Date (hours): {self.timesheet_ytd.paid_holiday_hours}')
        print(f'Paid Holiday Remaining (hours): {self.employee.paid_holidays - self.timesheet_ytd.paid_holiday_hours}')
        print(f'Paid Sick Time Used To-Date (hours): {self.timesheet_ytd.paid_sick_hours}')
        print(f'Paid Sick Time Remaining (hours): {self.employee.paid_sick - self.timesheet_ytd.paid_sick_hours}')


class EAMSQuarterlyReport:
    """Generates reports for Washington State quarterly reporting in the EAMS tool."""
    def __init__(self, data: DataProvider, year: int, quarter: int):
        self.data_provider = data
        self.employer = self.data_provider.employer

        self.reports = []

        self.year = year
        self.start_date = None
        self.end_date = None
        self.get_date_range(quarter)
        self.calculate()

    def get_date_range(self, quarter):
        """Populates start and end dates for the provided quarter of year."""
        if quarter == 1:
            self.start_date = Date(self.year, 1, 1)
            self.end_date = Date(self.year, 3, 31)
        elif quarter == 2:
            self.start_date = Date(self.year, 4, 1)
            self.end_date = Date(self.year, 6, 30)
        elif quarter == 3:
            self.start_date = Date(self.year, 7, 1)
            self.end_date = Date(self.year, 9, 30)
        elif quarter == 4:
            self.start_date = Date(self.year, 10, 1)
            self.end_date = Date(self.year, 12, 31)
        else:
            raise IOError(f"Provided 'quarter' value of '{quarter}' is invalid. Valid inputs: 1, 2, 3, or 4.")

    def calculate(self):
        """Builds a report for each employee from the current date range."""
        self.reports = []

        for employee in self.data_provider.employees:
            time_entries = self.data_provider.get_worked_time_in_range(employee, self.start_date, self.end_date)
            if not time_entries:
                print(f'WARNING: No time entries found for {employee.name} in the provided date range.')

            report = QuarterlyReportValues()
            report.employee = employee
            for time_entry in time_entries:
                report.add_time_entry(time_entry)

            self.reports.append(report)

    def to_csv(self, file_path: Path):
        """Writes the reports out to csv format. This is useful for importing directly into the EAMS website."""
        rows = []
        for report in self.reports:
            row = [report.employee.ssn,
                   report.employee.last_name,
                   report.employee.first_name,
                   report.employee.middle_name,
                   "",  # suffix
                   math.ceil(report.hours),  # EAMS tool requires whole numbers, no decimals
                   report.gross_pay,
                   config.EAMS_OCCUPATIONAL_CODE]
            rows.append(row)

        # writing to csv file
        with open(file_path, "w", newline="") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(rows)

    def to_console(self):
        """Prints the reports."""
        for report in self.reports:
            print(f"{report.employee.ssn}, "
                  f"{report.employee.last_name}, "
                  f"{report.employee.first_name}, "
                  f"{report.employee.middle_name}, "
                  f"{report.hours}, "
                  f"{report.gross_pay}, "
                  f"{config.EAMS_OCCUPATIONAL_CODE}")
