"""Code to output a parsed flattened JSON schema in various spreadsheet
formats."""

from schema import SchemaParser
import xlsxwriter
import csv
import os


class SpreadsheetOutput():
    def __init__(self, parser, main_sheet_name='main'):
        self.parser = parser
        self.main_sheet_name = main_sheet_name

    def open(self):
        pass

    def write_sheet(self, sheet_name, sheet_header):
        raise NotImplementedError

    def write_sheets(self):
        self.open()

        self.write_sheet(self.main_sheet_name, self.parser.main_sheet)
        for sheet_name, sheet_header in sorted(self.parser.sub_sheets.items()):
            self.write_sheet(sheet_name, sheet_header)

        self.close()

    def close(self):
        pass


class XlsxOutput(SpreadsheetOutput):
    def open(self):
        self.workbook = xlsxwriter.Workbook('release.xlsx')

    def write_sheet(self, sheet_name, sheet_header):
        worksheet = self.workbook.add_worksheet(sheet_name)
        for i, field in enumerate(sheet_header):
            worksheet.write(0, i, field)

    def close(self):
        self.workbook.close()


class CSVDirectoryOutupt(SpreadsheetOutput):
    def open(self):
        try:
            os.makedirs('release')
        except OSError:
            pass

    def write_sheet(self, sheet_name, sheet_header):
        with open(os.path.join('release', sheet_name+'.csv'), 'w') as csv_file:
            csv_sheet = csv.writer(csv_file)
            csv_sheet.writerow(sheet_header)


FORMATS = {
    'xlsx': XlsxOutput,
    'csvdir': CSVDirectoryOutupt
}


def output_release_schema_all_formats():
    parser = SchemaParser(schema_filename='release-schema.json')
    parser.parse()
    for spreadsheet_output_class in FORMATS.values():
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name='release')
        spreadsheet_output.write_sheets()


if __name__ == '__main__':
    output_release_schema_all_formats()
