"""This helper function is for parsing the Percentage Method Tables from IRS publication 15-T.

It is built to read a text file that is copy and pasted out of the PDF and format it into
json data that can be added to the tax_rates.json file."""

import json


def float_or_int(value):
    try:
        return int(value)
    except ValueError:
        return float(value)


out_dict = {"MultipleJobsNotChecked": {"Married": [], "Single": [], "Head": []},
            "MultipleJobsChecked": {"Married": [], "Single": [], "Head": []}}

lines = []
with open(r"stub_data\percentage_table.txt", "r") as infile:
    in_lines = [line for line in infile]
    for i, raw_line in enumerate(in_lines):
        lines.append(raw_line.rstrip())

headers = lines[0].split(" ")
col_split = len(headers) // 2  # find the colum split point

group = 0
for line in lines[1:]:
    row_list = line.split(" ")
    if row_list[0] == "Married":
        group = 1
        continue
    if row_list[0] == "Single":
        group = 2
        continue
    if row_list[0] == "Head":
        group = 3
        continue

    # fill in gaps in last row
    if len(row_list) < len(headers):
        row_list.insert(1, "-1")
        row_list.insert(6, "-1")

    # strip out string formatting
    clean_list = [item.strip("$").strip("%").replace(",", "") for item in row_list]

    # split into "Multiple Jobs Not Checked" and "Multiple Jobs Checked" columns
    not_checked = clean_list[:col_split]
    checked = clean_list[col_split:]

    if group == 1:
        col_dict = {}
        for key, value in zip(headers, not_checked):
            col_dict[key] = float_or_int(value)
        out_dict["MultipleJobsNotChecked"]["Married"].append(col_dict)

        col_dict = {}
        for key, value in zip(headers, checked):
            col_dict[key] = float_or_int(value)
        out_dict["MultipleJobsChecked"]["Married"].append(col_dict)

    if group == 2:
        col_dict = {}
        for key, value in zip(headers, not_checked):
            col_dict[key] = float_or_int(value)
        out_dict["MultipleJobsNotChecked"]["Single"].append(col_dict)

        col_dict = {}
        for key, value in zip(headers, checked):
            col_dict[key] = float_or_int(value)
        out_dict["MultipleJobsChecked"]["Single"].append(col_dict)

    if group == 3:
        col_dict = {}
        for key, value in zip(headers, not_checked):
            col_dict[key] = float_or_int(value)
        out_dict["MultipleJobsNotChecked"]["Head"].append(col_dict)

        col_dict = {}
        for key, value in zip(headers, checked):
            col_dict[key] = float_or_int(value)
        out_dict["MultipleJobsChecked"]["Head"].append(col_dict)

out_data = json.dumps(out_dict)
print(out_data)  # copy and paste this into the tax_rates year
