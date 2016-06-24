"""
This file has classes describing input from spreadsheets.

"""

from __future__ import print_function
from __future__ import unicode_literals
import sys
from decimal import Decimal, InvalidOperation
import os
import codecs
from collections import OrderedDict

import openpyxl
from six import text_type
from warnings import warn
import traceback
import datetime
import json
import pytz
from openpyxl.utils import _get_column_letter, column_index_from_string
from flattentool.lib import decimal_default, Cell
import tempfile

WITH_CELLS = True


# The "pylint: disable" lines exist to ignore warnings about the imports we expect not to work not working

if sys.version > '3':
    from csv import DictReader
    from csv import reader as csvreader
else:
    from unicodecsv import DictReader  # pylint: disable=F0401
    from unicodecsv import reader as csvreader  # pylint: disable=F0401

try:
    from collections import UserDict  # pylint: disable=E0611
except ImportError:
    from UserDict import UserDict  # pylint: disable=F0401

def convert_type(type_string, value, timezone = pytz.timezone('UTC')):
    if value == '' or value is None:
        return None
    if type_string == 'number':
        try:
            return Decimal(value)
        except (TypeError, ValueError, InvalidOperation):
            warn('Non-numeric value "{}" found in number column, returning as string instead.'.format(value))
            return text_type(value)
    elif type_string == 'integer':
        try:
            return int(value)
        except (TypeError, ValueError):
            warn('Non-integer value "{}" found in integer column, returning as string instead.'.format(value))
            return text_type(value)
    elif type_string == 'boolean':
        value = text_type(value)
        if value.lower() in ['true', '1']:
            return True
        elif value.lower() in ['false', '0']:
            return False
        else:
            warn('Unrecognised value for boolean: "{}", returning as string instead'.format(value))
            return text_type(value)
    elif type_string in ('array', 'array_array', 'string_array'):
        value = text_type(value)
        if ',' in value:
            return [x.split(',') for x in value.split(';')]
        else:
            return value.split(';')
    elif type_string == 'string':
        if type(value) == datetime.datetime:
            return timezone.localize(value).isoformat()
        return text_type(value)
    elif type_string == '':
        if type(value) == datetime.datetime:
            return timezone.localize(value).isoformat()
        return value if type(value) in [int] else text_type(value)
    else:
        raise ValueError('Unrecognised type: "{}"'.format(type_string))


def merge(base, mergee, debug_info=None):
    if not debug_info:
        debug_info = {}
    for key, v in mergee.items():
        if WITH_CELLS and isinstance(v, Cell):
            value = v.cell_value
        else:
            value = v
        if key in base:
            if isinstance(value, TemporaryDict):
                for temporarydict_key, temporarydict_value in value.items():
                    if temporarydict_key in base[key]:
                        merge(base[key][temporarydict_key], temporarydict_value, debug_info)
                    else:
                        assert temporarydict_key not in base[key], 'Overwriting cell {} by mistake'.format(temporarydict_value)
                        base[key][temporarydict_key] = temporarydict_value
                for temporarydict_value in  value.items_no_keyfield:
                    base[key].items_no_keyfield.append(temporarydict_value)
            elif isinstance(value, dict) and isinstance(base[key], dict):
                merge(base[key], value, debug_info)
            else:
                if WITH_CELLS:
                    base_value = base[key].cell_value
                else:
                    base_value = base[key]
                if base_value != value:
                    id_info = 'id "{}"'.format(debug_info.get('id'))
                    if debug_info.get('root_id'):
                        id_info = '{} "{}", '.format(debug_info.get('root_id'), debug_info.get('root_id_or_none'))+id_info
                    warn('Conflict when merging field "{}" for {} in sheet {}: "{}" != "{}". If you were not expecting merging you may have a duplicate ID.'.format(
                        key, id_info, debug_info.get('sheet_name'), base_value, value))
                else:
                    if WITH_CELLS:
                        base[key].sub_cells.append(v)
        else:
            # This happens when a parent record finds the first a child record of a known type
            if WITH_CELLS: # Either way, we still want to pass back either the cell or the value
                base[key] = v
            else:
                base[key] = v

class SpreadsheetInput(object):
    """
    Base class describing a spreadsheet input. Has stubs which are
    implemented via inheritance for particular types of spreadsheet (e.g. xlsx
    or csv).

    """
    def convert_dict_titles(self, dicts, title_lookup=None):
        """
        Replace titles with field names in the given list of dictionaries
        (``dicts``) using the titles lookup in the schema parser.

        """
        if self.parser:
            title_lookup = title_lookup or self.parser.title_lookup
        for d in dicts:
            if title_lookup:
                yield OrderedDict([(title_lookup.lookup_header(k), v) for k,v in d.items()])
            else:
                yield d

    def __init__(self, input_name='', root_list_path='main', timezone_name='UTC', root_id='ocid', convert_titles=False):
        self.input_name = input_name
        self.root_list_path = root_list_path
        self.sub_sheet_names = []
        self.timezone = pytz.timezone(timezone_name)
        self.root_id = root_id
        self.convert_titles = convert_titles
        self.parser = None

    def get_sub_sheets_lines(self):
        for sub_sheet_name in self.sub_sheet_names:
            if self.convert_titles:
                yield sub_sheet_name, self.convert_dict_titles(self.get_sheet_lines(sub_sheet_name),
                    self.parser.sub_sheets[sub_sheet_name].title_lookup if sub_sheet_name in self.parser.sub_sheets else None)
            else:
                yield sub_sheet_name, self.get_sheet_lines(sub_sheet_name)

    def get_sheet_lines(self, sheet_name):
        raise NotImplementedError

    def get_sheet_headings(self, sheet_name):
        raise NotImplementedError

    def read_sheets(self):
        raise NotImplementedError

    # XXX This method does not appear to get called, could it be deleted?
    def convert_types(self, in_dict):
        out_dict = OrderedDict()
        for key, value in in_dict.items():
            parts = key.split(':')
            if len(parts) > 1:
                out_dict[parts[0]] = convert_type(parts[1], value, self.timezone)
            else:
                out_dict[parts[0]] = convert_type('', value, self.timezone)
        return out_dict


    def do_unflatten(self):
        main_sheet_by_ocid = OrderedDict()
        sheets = list(self.get_sub_sheets_lines())
        for i, sheet in enumerate(sheets):
            sheet_name, lines = sheet
            try:
                actual_headings = self.get_sheet_headings(sheet_name)
            except NotImplementedError:
                # The ListInput type used in the tests doesn't support getting headings.
                actual_headings = None
            for j, line in enumerate(lines):
                if all(x is None or x == '' for x in line.values()):
                #if all(x == '' for x in line.values()):
                    continue
                root_id_or_none = line[self.root_id] if self.root_id else None
                if WITH_CELLS:
                    cells = OrderedDict()
                    for k, header in enumerate(line):
                        if actual_headings:
                            cells[header] = Cell(line[header], (sheet_name, _get_column_letter(k+1), j+2, actual_headings[k]))
                        else:
                            cells[header] = Cell(line[header], (sheet_name, _get_column_letter(k+1), j+2, header))
                    unflattened = unflatten_main_with_parser(self.parser, cells, self.timezone)
                else:
                    unflattened = unflatten_main_with_parser(self.parser, line, self.timezone)
                if root_id_or_none not in main_sheet_by_ocid:
                    main_sheet_by_ocid[root_id_or_none] = TemporaryDict('id')
                def inthere(unflattened, id_name):
                    if WITH_CELLS:
                        return unflattened[id_name].cell_value
                    else:
                        return unflattened[id_name]
                if 'id' in unflattened and inthere(unflattened, 'id') in main_sheet_by_ocid[root_id_or_none]:
                    if WITH_CELLS:
                        unflattened_id = unflattened.get('id').cell_value
                    else:
                        unflattened_id = unflattened.get('id')
                    merge(
                        main_sheet_by_ocid[root_id_or_none][unflattened_id],
                        unflattened,
                        {
                            'sheet_name': sheet_name,
                            'root_id': self.root_id,
                            'root_id_or_none': root_id_or_none,
                            'id': unflattened_id
                        }
                    )
                else:
                    main_sheet_by_ocid[root_id_or_none].append(unflattened)
        temporarydicts_to_lists(main_sheet_by_ocid)

        return sum(main_sheet_by_ocid.values(), [])


    def unflatten(self):
        if WITH_CELLS:
            tmp_directory = tempfile.mkdtemp()
            file_name = os.path.join(tmp_directory, 'unflattened.json')
            self.results_from_cell_tree({}, 'main', file_name)
            with open(file_name) as unflattened:
                return json.load(unflattened, object_pairs_hook=OrderedDict)['main']
        return self.do_unflatten()


    def extract_error_path(self, cell_tree):
        return sorted(extract_list_to_error_path([self.root_list_path], cell_tree).items())


    def results_from_cell_tree(self, base, main_sheet_name, output_name):
        cell_tree = self.do_unflatten()
        base[main_sheet_name] = cell_tree
        with codecs.open(output_name, 'w', encoding='utf-8') as fp:
            json.dump(base, fp, indent=4, default=decimal_default, ensure_ascii=False)
        return self.extract_error_path(cell_tree)


    def fancy_unflatten(self, base, main_sheet_name, output_name, cell_source_map, heading_source_map):
        if not WITH_CELLS:
            raise Exception('Can only do a fancy_unflatten() if WITH_CELLS=True')
        ordered_items = self.results_from_cell_tree(base, main_sheet_name, output_name)
        if not cell_source_map and not heading_source_map:
            return
        row_source_map = OrderedDict()
        heading_source_map_data = OrderedDict()
        for path, cells in ordered_items:
            # Prepare row_source_map key
            key = '/'.join(str(x) for x in path[:-1])
            if not key in row_source_map:
                row_source_map[key] = []
            # Prepeare header_source_map key
            header_path_parts = []
            for x in path:
                try:
                    int(x)
                except:
                    header_path_parts.append(x)
            header_path = '/'.join(header_path_parts)
            if header_path not in heading_source_map_data:
                heading_source_map_data[header_path] = []
            # Populate the row and header source maps
            for cell in cells:
                sheet, col, row, header = cell
                if (sheet, row) not in row_source_map[key]:
                    row_source_map[key].append((sheet, row))
                if (sheet, header) not in heading_source_map_data[header_path]:
                    heading_source_map_data[header_path].append((sheet, header))
        for key in row_source_map:
            ordered_items.append((key.split('/'), row_source_map[key]))

        if cell_source_map:
            with codecs.open(cell_source_map, 'w', encoding='utf-8') as fp:
                json.dump(
                    OrderedDict(( '/'.join(str(x) for x in path), location) for path, location in ordered_items),
                    fp, default=decimal_default, ensure_ascii=False, indent=4
                )
        if heading_source_map:
            with codecs.open(heading_source_map, 'w', encoding='utf-8') as fp:
                json.dump(heading_source_map_data, fp, indent=4, default=decimal_default, ensure_ascii=False)


def extract_list_to_error_path(path, input):
    output = {}
    for i, item in enumerate(input):
        res = extract_dict_to_error_path(path + [i], item)
        for p in res:
            assert p not in output, 'Already have key {}'.format(p)
            output[p] = res[p]
    return output

def extract_dict_to_error_path(path, input):
    output = {}
    for k in input:
        if isinstance(input[k], list):
            res = extract_list_to_error_path(path+[k], input[k])
            for p in res:
                assert p not in output, 'Already have key {}'.format(p)
                output[p] = res[p]
        elif isinstance(input[k], dict):
            res = extract_dict_to_error_path(path+[k], input[k])
            for p in res:
                assert p not in output, 'Already have key {}'.format(p)
                output[p] = res[p]
        elif isinstance(input[k], Cell):
            p = tuple(path+[k])
            assert p not in output, 'Already have key {}'.format(p)
            output[p] = [input[k].cell_location]
            for sub_cell in input[k].sub_cells:
                assert sub_cell.cell_value == input[k].cell_value, 'Two sub-cells have different values: {}, {}'.format(input[k].cell_value, sub_cell.cell_value)
                output[p].append(sub_cell.cell_location)
        else:
            raise Exception('Unexpected result type in the JSON cell tree: {}'.format(input[k]))
    return output


class CSVInput(SpreadsheetInput):
    encoding = 'utf-8'

    def get_sheet_headings(self, sheet_name):
        if sys.version > '3':  # If Python 3 or greater
            with open(os.path.join(self.input_name, sheet_name+'.csv'), encoding=self.encoding) as main_sheet_file:
                r = csvreader(main_sheet_file)
                for row in enumerate(r):
                    # Just return the first row
                    return row[1]
        else:  # If Python 2
            with open(os.path.join(self.input_name, sheet_name+'.csv')) as main_sheet_file:
                r = csvreader(main_sheet_file, encoding=self.encoding)
                for row in enumerate(r):
                    # Just return the first row
                    return row[1]

    def read_sheets(self):
        sheet_file_names = os.listdir(self.input_name)
        self.sub_sheet_names = sorted([fname[:-4] for fname in sheet_file_names if fname.endswith('.csv')])

    def get_sheet_lines(self, sheet_name):
        if sys.version > '3':  # If Python 3 or greater
            # Pass the encoding to the open function
            with open(os.path.join(self.input_name, sheet_name+'.csv'), encoding=self.encoding) as main_sheet_file:
                dictreader = DictReader(main_sheet_file)
                for line in dictreader:
                    yield OrderedDict((fieldname, line[fieldname]) for fieldname in dictreader.fieldnames)
        else:  # If Python 2
            # Pass the encoding to DictReader
            with open(os.path.join(self.input_name, sheet_name+'.csv')) as main_sheet_file:
                dictreader = DictReader(main_sheet_file, encoding=self.encoding)
                for line in dictreader:
                    yield OrderedDict((fieldname, line[fieldname]) for fieldname in dictreader.fieldnames)


class XLSXInput(SpreadsheetInput):
    def read_sheets(self):
        self.workbook = openpyxl.load_workbook(self.input_name, data_only=True)

        self.sheet_names_map = OrderedDict((sheet_name, sheet_name) for sheet_name in self.workbook.get_sheet_names())

        sheet_names = list(self.sheet_names_map.keys())
        self.sub_sheet_names = sheet_names

    def get_sheet_headings(self, sheet_name):
        worksheet = self.workbook[self.sheet_names_map[sheet_name]]
        return [cell.value for cell in worksheet.rows[0]]

    def get_sheet_lines(self, sheet_name):
        worksheet = self.workbook[self.sheet_names_map[sheet_name]]
        header_row = worksheet.rows[0]
        remaining_rows = worksheet.rows[1:]
        coli_to_header = ({i: x.value for i, x in enumerate(header_row) if x.value is not None})
        for row in remaining_rows:
            yield OrderedDict((coli_to_header[i], x.value) for i, x in enumerate(row) if i in coli_to_header)


FORMATS = {
    'xlsx': XLSXInput,
    'csv': CSVInput
}


def unflatten_line(line):
    unflattened = OrderedDict()
    for k, v in line.items():
        if v is None:
            continue
        fields = k.split('/')
        path_search(unflattened, fields[:-1], top_sheet=True)[fields[-1]] = v
    return unflattened

def isint(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

class ListAsDict(dict):
    pass

def list_as_dicts_to_temporary_dicts(unflattened):
    for key, value in list(unflattened.items()):
        if WITH_CELLS and isinstance(value, Cell):
            continue
        if hasattr(value, 'items'):
            if not value:
                unflattened.pop(key)
            list_as_dicts_to_temporary_dicts(value)
        if isinstance(value, ListAsDict):
            temporarydict = TemporaryDict("id")
            for index in sorted(value.keys()):
                temporarydict.append(value[index])
            unflattened[key] = temporarydict
    return unflattened


def unflatten_main_with_parser(parser, line, timezone):
    unflattened = OrderedDict()
    for path, input in line.items():
        # Skip blank cells
        if WITH_CELLS:
            cell = input
            if cell.cell_value is None or cell.cell_value == '':
                continue
        else:
            value = input
            if value is None or value == '':
                continue
        current_path = unflattened
        path_list = [item.rstrip('[]') for item in path.split('/')]
        for num, path_item in enumerate(path_list):
            if isint(path_item):
                continue
            path_till_now = '/'.join([item for item in path_list[:num+1] if not isint(item)])
            if parser:
                current_type = parser.flattened.get(path_till_now)
            else:
                current_type = None
            try:
                next_path_item = path_list[num+1]
            except IndexError:
                next_path_item = ''

            ## Array
            list_index = -1
            if isint(next_path_item):
                if current_type and current_type != 'array':
                    raise ValueError("There is an array at '{}' when the schema says there should be a '{}'".format(path_till_now, current_type))
                list_index = int(next_path_item)

            if isint(next_path_item) or current_type == 'array':
                list_as_dict = current_path.get(path_item)
                if list_as_dict is None:
                    list_as_dict = ListAsDict()
                    current_path[path_item] = list_as_dict
                new_path = list_as_dict.get(list_index)
                if new_path is None:
                    new_path = OrderedDict()
                    list_as_dict[list_index] = new_path
                current_path = new_path
                continue

            ## Object
            if current_type == 'object' or (not current_type and next_path_item):
                new_path = current_path.get(path_item)
                if new_path is None:
                    new_path = OrderedDict()
                    current_path[path_item] = new_path
                current_path = new_path
                continue
            if current_type and current_type != 'object' and next_path_item:
                raise ValueError("There is an object or list at '{}' but it should be an {}".format(path_till_now, current_type))

            ## Other Types
            if WITH_CELLS:
                value = cell.cell_value
                converted_value = convert_type(current_type or '', value, timezone)
                cell.cell_value = converted_value
                if converted_value is not None and converted_value != '':
                    current_path[path_item] = cell
            else:
                converted_value = convert_type(current_type or '', value, timezone)
                if converted_value is not None and converted_value != '':
                    current_path[path_item] = converted_value

    unflattened = list_as_dicts_to_temporary_dicts(unflattened)
    return unflattened



class IDFieldMissing(KeyError):
    pass


def path_search(nested_dict, path_list, id_fields=None, path=None, top=False, top_sheet=False):
    if not path_list:
        return nested_dict

    id_fields = id_fields or {}
    parent_field = path_list[0]
    path = parent_field if path is None else path+'/'+parent_field

    if parent_field.endswith('[]') or top:
        if parent_field.endswith('[]'):
            parent_field = parent_field[:-2]
        if parent_field not in nested_dict:
            nested_dict[parent_field] = TemporaryDict(keyfield='id', top_sheet=top_sheet)
        sub_sheet_id = id_fields.get(path+'/id')
        if sub_sheet_id not in nested_dict[parent_field]:
            nested_dict[parent_field][sub_sheet_id] = {}
        return path_search(nested_dict[parent_field][sub_sheet_id],
                           path_list[1:],
                           id_fields=id_fields,
                           path=path,
                           top_sheet=top_sheet)
    else:
        if parent_field not in nested_dict:
            nested_dict[parent_field] = OrderedDict()
        return path_search(nested_dict[parent_field],
                           path_list[1:],
                           id_fields=id_fields,
                           path=path,
                           top_sheet=top_sheet)


class TemporaryDict(UserDict):
    __slots__ = ['keyfield', 'items_no_keyfield', 'data', 'top_sheet']
    def __init__(self, keyfield, top_sheet=False):
        self.keyfield = keyfield
        self.items_no_keyfield = []
        self.data = OrderedDict()
        self.top_sheet = top_sheet

    def __repr__(self):
        return 'TemporaryDict(keyfield={}, items_no_keyfield={}, data={})'.format(repr(self.keyfield), repr(self.items_no_keyfield), repr(self.data))

    def append(self, item):
        if self.keyfield in item:
            if WITH_CELLS and isinstance(item[self.keyfield], Cell):
                key = item[self.keyfield].cell_value
            else:
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
        if isinstance(value, Cell):
            continue
        if hasattr(value, 'to_list'):
            temporarydicts_to_lists(value)
            if hasattr(value, 'items_no_keyfield'):
                for x in value.items_no_keyfield:
                    temporarydicts_to_lists(x)
            nested_dict[key] = value.to_list()
        elif hasattr(value, 'items'):
            temporarydicts_to_lists(value)


class ConflictingIDFieldsError(ValueError):
    pass


def find_deepest_id_field(id_fields):
    split_id_fields = [x.split('/') for x in id_fields]
    deepest_id_field = max(split_id_fields, key=len)
    for split_id_field in split_id_fields:
        if not all(deepest_id_field[i] == x for i, x in enumerate(split_id_field[:-1])):
            raise ConflictingIDFieldsError()
    return '/'.join(deepest_id_field)

