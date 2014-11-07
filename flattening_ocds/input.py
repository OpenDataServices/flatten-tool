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

    def read_sheets(self):
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
            for line in reader:
                yield line


def unflatten_line(line):
    unflattened = {}
    for k, v in line.items():
        if v == '':
            continue
        fields = k.split('/')
        path_search(unflattened, fields[:-1])[fields[-1]] = v
    return unflattened


def path_search(nested_dict, path_list):
    nested_dict = nested_dict
    for parent_field in path_list:
        if parent_field not in nested_dict:
            nested_dict[parent_field] = {}
        nested_dict = nested_dict[parent_field]
    return nested_dict

def unflatten_spreadsheet_input(spreadsheet_input):
    main_sheet_by_ocid = {}
    for line in spreadsheet_input.get_main_sheet_lines():
        if line['ocid'] in main_sheet_by_ocid:
            raise ValueError('Two lines in main spreadsheet with same ocid')
        main_sheet_by_ocid[line['ocid']] = unflatten_line(line)

    for sheet_name, lines in spreadsheet_input.get_sub_sheets_lines():
        for line in lines:
            id_fields = [ x for x in line.keys() if x.endswith('/id') ]
            line_without_id_fields = {k: v for k, v in line.items() if k not in id_fields and k!='ocid'}
            if not all(x.startswith(spreadsheet_input.main_sheet_name) for x in id_fields):
                raise ValueError
            for id_field in id_fields:
                if line[id_field]:
                    context = path_search(
                        main_sheet_by_ocid[line['ocid']],
                        id_field.split('/')[1:-1]
                    )
                    if sheet_name not in context:
                        context[sheet_name] = []
                    context[sheet_name].append(unflatten_line(line_without_id_fields))

    return main_sheet_by_ocid.values()
