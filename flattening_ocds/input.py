from __future__ import print_function
from csv import DictReader
import os
import json


class SpreadsheetInput(object):
    def __init__(self, input_name='', main_sheet_name=''):
        self.input_name = input_name
        self.main_sheet_name = main_sheet_name
        self.sub_sheets_names = []

    def get_main_sheet_lines(self):
        return self.get_sheet_lines(self.main_sheet_name)

    def get_sub_sheets_lines(self):
        for sub_sheet_name in self.sub_sheets_names:
            yield sub_sheet_name, self.get_sheet_lines(sub_sheet_name)

    def get_sheet_lines(self, sheet_name):
        raise NotImplementedError


class CSVInput(SpreadsheetInput):
    def read_sheets(self):
        sheet_file_names = os.listdir(self.input_name)
        if self.main_sheet_name+'.csv' not in sheet_file_names:
            raise ValueError
        sheet_file_names.remove(self.main_sheet_name+'.csv')

        if not all([fname.endswith('.csv') for fname in sheet_file_names]):
            raise ValueError
        self.sub_sheet_names = [fname[:-4] for fname in sheet_file_names]

    def get_sheet_lines(self, sheet_name):
        with open(os.path.join(self.input_name, sheet_name+'.csv')) as main_sheet_file:
            for line in DictReader(main_sheet_file):
                yield line


def unflatten_line(line):
    unflattened = {}
    for k, v in line.items():
        if v == '':
            continue
        fields = k.split('.')
        unlattened_sub_dict = unflattened
        for parent_field in fields[:-1]:
            if parent_field not in unlattened_sub_dict:
                unlattened_sub_dict[parent_field] = {}
            unlattened_sub_dict = unlattened_sub_dict[parent_field]
        unlattened_sub_dict[fields[-1]] = v
    return unflattened


def unflatten(spreadsheet_input):
    main_sheet_by_ocid = {}
    for line in spreadsheet_input.get_main_sheet_lines():
        if line['ocid'] in main_sheet_by_ocid:
            raise ValueError('Two lines in main spreadsheet with same ocid')
        main_sheet_by_ocid[line['ocid']] = unflatten_line(line)

    for sheet_name, lines in spreadsheet_input.get_sub_sheets_lines():
        for line in lines:
            main_sheet_by_ocid[line['ocid']][sheet_name] = unflatten_line(line)

    return main_sheet_by_ocid.values()


if __name__ == '__main__':
    spreadsheet_input = CSVInput(input_name='release_input', main_sheet_name='release')
    spreadsheet_input.read_sheets()
    print(json.dumps(list(unflatten(spreadsheet_input)), indent=2))
