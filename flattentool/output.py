"""
Code to output a parsed flattened JSON schema in various spreadsheet
formats.

"""

import openpyxl
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
import csv
import os
import sys
from warnings import warn
import six
from flattentool.exceptions import DataErrorWarning

if sys.version > '3':
    import csv
else:
    import unicodecsv as csv  # pylint: disable=F0401


class SpreadsheetOutput(object):
    # output_name is given a default here, partly to help with tests,
    # but should have been defined by the time we get here.
    def __init__(self, parser, main_sheet_name='main', output_name='unflattened', sheet_prefix=''):
        self.parser = parser
        self.main_sheet_name = main_sheet_name
        self.output_name = output_name
        self.sheet_prefix = sheet_prefix

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
        worksheet.append(sheet_header)
        for sheet_line in sheet.lines:
            line = []
            for header in sheet_header:
                value = sheet_line.get(header)
                if isinstance(value, six.text_type):
                    new_value = ILLEGAL_CHARACTERS_RE.sub('', value)
                    if new_value != value:
                        warn("Character(s) in '{}' are not allowed in a spreadsheet cell. Those character(s) will be removed".format(value),
                            DataErrorWarning)
                    value = new_value
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
        if sys.version > '3':  # If Python 3 or greater
            # Pass the encoding to the open function
            with open(os.path.join(self.output_name, self.sheet_prefix + sheet_name+'.csv'), 'w', encoding='utf-8') as csv_file:
                dictwriter = csv.DictWriter(csv_file, sheet_header)
                dictwriter.writeheader()
                for sheet_line in sheet.lines:
                    dictwriter.writerow(sheet_line)
        else:  # If Python 2
            # Pass the encoding to DictReader
            with open(os.path.join(self.output_name, self.sheet_prefix + sheet_name+'.csv'), 'w') as csv_file:
                dictwriter = csv.DictWriter(csv_file, sheet_header, encoding='utf-8')
                dictwriter.writeheader()
                for sheet_line in sheet.lines:
                    dictwriter.writerow(sheet_line)


FORMATS = {
    'xlsx': XLSXOutput,
    'csv': CSVOutput
}
FORMATS_SUFFIX = {
    'xlsx': '.xlsx',
    'csv': ''  # This is the suffix for the directory
}
