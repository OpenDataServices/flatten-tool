"""
Code to output a parsed flattened JSON schema in various spreadsheet
formats.

"""

import csv
import os
from warnings import warn

import odf.table
import odf.text
import openpyxl
from odf.opendocument import OpenDocumentSpreadsheet
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from flattentool.exceptions import DataErrorWarning


def sanitise(value):
    if isinstance(value, str):
        new_value = ILLEGAL_CHARACTERS_RE.sub("", value)
        if new_value != value:
            warn(
                "Character(s) in '{}' are not allowed in a spreadsheet cell. Those character(s) will be removed".format(
                    value
                ),
                DataErrorWarning,
            )
        return new_value
    else:
        return value


class SpreadsheetOutput(object):
    # output_name is given a default here, partly to help with tests,
    # but should have been defined by the time we get here.
    def __init__(
        self,
        parser,
        main_sheet_name="main",
        output_name="unflattened",
        sheet_prefix="",
        vertical_orientation=False,
    ):
        self.parser = parser
        self.main_sheet_name = main_sheet_name
        self.output_name = output_name
        self.sheet_prefix = sheet_prefix
        self.vertical_orientation = vertical_orientation

    def open(self):
        pass

    def write_sheet(self, sheet_name, sheet_header, sheet_lines=None):
        raise NotImplementedError

    def write_sheets(self):
        self.open()

        self.write_sheet(self.main_sheet_name, self.parser.main_sheet)
        for sheet_name, sub_sheet in sorted(self.parser.sub_sheets.items()):
            self.write_sheet(sheet_name, sub_sheet)

        self.close()

    def close(self):
        pass


class XLSXOutput(SpreadsheetOutput):
    def open(self):
        self.workbook = openpyxl.Workbook()

    def write_sheet(self, sheet_name, sheet):
        sheet_header = list(sheet)
        worksheet = self.workbook.create_sheet()
        worksheet.title = self.sheet_prefix + sheet_name
        if self.vertical_orientation:
            for header in sheet_header:
                line = []
                line.append(header)
                for sheet_line in sheet.lines:
                    value = sanitise(sheet_line.get(header))
                    line.append(value)
                worksheet.append(line)

        else:
            worksheet.append(sheet_header)
            for sheet_line in sheet.lines:
                line = []
                for header in sheet_header:
                    value = sanitise(sheet_line.get(header))
                    line.append(value)
                worksheet.append(line)

    def close(self):
        self.workbook.remove(self.workbook.active)
        self.workbook.save(self.output_name)


class CSVOutput(SpreadsheetOutput):
    def open(self):
        try:
            os.makedirs(self.output_name)
        except OSError:
            pass

    def write_sheet(self, sheet_name, sheet):
        sheet_header = list(sheet)
        with open(
            os.path.join(self.output_name, self.sheet_prefix + sheet_name + ".csv"),
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            dictwriter = csv.DictWriter(csv_file, sheet_header)
            dictwriter.writeheader()
            for sheet_line in sheet.lines:
                dictwriter.writerow(sheet_line)


class ODSOutput(SpreadsheetOutput):
    def open(self):
        self.workbook = OpenDocumentSpreadsheet()

    def _make_cell(self, value):
        """ Util for creating an ods cell """

        if value:
            try:
                # See if value parses as a float
                cell = odf.table.TableCell(valuetype="float", value=float(value))
            except ValueError:
                cell = odf.table.TableCell(valuetype="string")
        else:
            cell = odf.table.TableCell(valuetype="Nonetype")

        p = odf.text.P(text=value)
        cell.addElement(p)

        return cell

    def write_sheet(self, sheet_name, sheet):

        worksheet = odf.table.Table(name=sheet_name)
        sheet_header = list(sheet)

        if self.vertical_orientation:
            for header in sheet_header:
                row = odf.table.TableRow()
                row.addElement(self._make_cell(header))
                for sheet_line in sheet.lines:
                    value = sanitise(sheet_line.get(header))
                    row.addElement(self._make_cell(value))
                worksheet.addElement(row)

        else:
            header_row = odf.table.TableRow()

            for header in sheet_header:
                header_row.addElement(self._make_cell(header))

            worksheet.addElement(header_row)

            for sheet_line in sheet.lines:
                row = odf.table.TableRow()
                for header in sheet_header:
                    value = sanitise(sheet_line.get(header))
                    row.addElement(self._make_cell(value))
                worksheet.addElement(row)

        self.workbook.spreadsheet.addElement(worksheet)

    def close(self):
        self.workbook.save(self.output_name)


FORMATS = {"xlsx": XLSXOutput, "csv": CSVOutput, "ods": ODSOutput}

FORMATS_SUFFIX = {
    "xlsx": ".xlsx",
    "ods": ".ods",
    "csv": "",  # This is the suffix for the directory
}
