from __future__ import print_function
from csv import DictReader
from decimal import Decimal
import os
import openpyxl
try:
    from collections import UserDict
except ImportError:
    from UserDict import UserDict


class SpreadsheetInput(object):
    def __init__(self, input_name='', main_sheet_name=''):
        self.input_name = input_name
        self.main_sheet_name = main_sheet_name
        self.sub_sheet_names = []

    def get_main_sheet_lines(self):
        return self.get_sheet_lines(self.main_sheet_name)

    def get_sub_sheets_lines(self):
        for sub_sheet_name in self.sub_sheet_names:
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

        self.sub_sheet_names = [fname[:-4] for fname in sheet_file_names if fname.endswith('.csv')]

    def get_sheet_lines(self, sheet_name):
        with open(os.path.join(self.input_name, sheet_name+'.csv')) as main_sheet_file:
            for line in DictReader(main_sheet_file):
                yield line


class XLSXInput(SpreadsheetInput):
    def read_sheets(self):
        self.workbook = openpyxl.load_workbook(self.input_name)
        sheet_names = self.workbook.get_sheet_names()
        if not self.main_sheet_name in sheet_names:
            raise ValueError
        sheet_names.remove(self.main_sheet_name)
        self.sub_sheet_names = sheet_names

    def get_sheet_lines(self, sheet_name):
        worksheet = self.workbook[sheet_name]
        header_row = worksheet.rows[0]
        remaining_rows = worksheet.rows[1:]
        coli_to_header = ({i:x.value for i, x in enumerate(header_row) if x.value is not None})
        for row in remaining_rows:
            yield {coli_to_header[i]:x.value for i, x in enumerate(row) if i in coli_to_header}


FORMATS = {
    'xlsx': XLSXInput,
    'csv': CSVInput
}


def unflatten_line(line):
    unflattened = {}
    for k, v in line.items():
        if v == '':
            continue
        fields = k.split('/')
        path_search(unflattened, fields[:-1])[fields[-1]] = v
    return unflattened


def path_search(nested_dict, path_list, id_fields=None, path=''):
    if not path_list:
        return nested_dict

    id_fields = id_fields or {}
    parent_field = path_list[0]
    path = path+'/'+parent_field

    if parent_field.endswith('[]'):
        parent_field = parent_field[:-2]
        if parent_field not in nested_dict:
            nested_dict[parent_field] = TemporaryDict(keyfield='id')
        sub_sheet_id = id_fields[path+'/id']
        if sub_sheet_id not in nested_dict[parent_field]:
            nested_dict[parent_field][sub_sheet_id] = {}
        return path_search(nested_dict[parent_field][sub_sheet_id],
                           path_list[1:], path=path)
    else:
        if parent_field not in nested_dict:
            nested_dict[parent_field] = {}
        return path_search(nested_dict[parent_field],
                           path_list[1:], path=path)


class TemporaryDict(UserDict):
    def __init__(self, keyfield):
        self.keyfield = keyfield
        self.items_no_keyfield = []
        UserDict.__init__(self)

    def append(self, item):
        if self.keyfield in item:
            key = item[self.keyfield]
            if key not in self.data:
                self.data[key] = item
            else:
                self.data[key].update(item)
        else:
            self.items_no_keyfield.append(item)

    def to_list(self):
        return list(self.data.values()) + self.items_no_keyfield


def temporarydicts_to_lists(nested_dict):
    """ Recrusively transforms TemporaryDicts to lists inplace. """
    for key, value in nested_dict.items():
        if hasattr(value, 'to_list'):
            temporarydicts_to_lists(value)
            nested_dict[key] = value.to_list()
        elif hasattr(value, 'items'):
            temporarydicts_to_lists(value)


def find_deepest_id_field(id_fields):
    split_id_fields = [x.split('/') for x in id_fields]
    deepest_id_field = max(split_id_fields, key=len)
    for split_id_field in split_id_fields:
        if not all(deepest_id_field[i] == x for i, x in enumerate(split_id_field[:-1])):
            raise ValueError
    return '/'.join(deepest_id_field)


def convert_type(type_string, value):
    if type_string == 'number':
        return Decimal(value)
    elif type_string == 'integer':
        return int(value)
    elif type_string == 'boolean':
        if value.lower() in ['true','1']:
            return True
        elif value.lower() in ['false','0']:
            return False
        else:
            raise ValueError('Unrecognised value for boolean: {}'.format(value))
    elif type_string == 'array':
        if ',' in value:
            return [ x.split(',') for x in value.split(';') ]
        else:
            return value.split(';')
    else:
        raise ValueError('Unrecognised type: {}'.format(type_string))

def convert_types(in_dict):
    out_dict = {}
    for key, value in in_dict.items():
        parts = key.split(':')
        if len(parts) > 1:
            out_dict[parts[0]] = convert_type(parts[1], value)
        else:
            out_dict[parts[0]] = value
    return out_dict


def unflatten_spreadsheet_input(spreadsheet_input):
    main_sheet_by_ocid = {}
    for line in spreadsheet_input.get_main_sheet_lines():
        if line['ocid'] in main_sheet_by_ocid:
            raise ValueError('Two lines in main spreadsheet with same ocid')
        main_sheet_by_ocid[line['ocid']] = unflatten_line(convert_types(line))

    for sheet_name, lines in spreadsheet_input.get_sub_sheets_lines():
        for line in lines:
            id_fields = {k: v for k, v in line.items() if
                k.split(':')[0].endswith('/id') and
                k.startswith(spreadsheet_input.main_sheet_name)}
            line_without_id_fields = {k: v for k, v in line.items() if k not in id_fields and k != 'ocid'}
            # FIXME add test for why this is wrong
            #if not all(x.startswith(spreadsheet_input.main_sheet_name) for x in id_fields):
            #    raise ValueError
            raw_id_fields_with_values = {k.split(':')[0]:v for k, v in id_fields.items() if v}
            sheet_context_names = {k.split(':')[0]:k.split(':')[1] if len(k.split(':')) > 1 else None for k, v in id_fields.items() if v}
            id_field = find_deepest_id_field(raw_id_fields_with_values)
            context = path_search(
                main_sheet_by_ocid[line['ocid']],
                id_field.split('/')[1:-1],
                id_fields=raw_id_fields_with_values,
                path=spreadsheet_input.main_sheet_name
            )
            sheet_context_name = sheet_context_names[id_field] or sheet_name
            if sheet_context_name not in context:
                context[sheet_context_name] = TemporaryDict(keyfield='id')
            context[sheet_context_name].append(unflatten_line(convert_types(line_without_id_fields)))
    temporarydicts_to_lists(main_sheet_by_ocid)

    return main_sheet_by_ocid.values()
