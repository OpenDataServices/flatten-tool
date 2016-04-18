"""
This file has classes describing input from spreadsheets.

"""

from __future__ import print_function
from __future__ import unicode_literals
import sys
from decimal import Decimal, InvalidOperation
import os
from collections import OrderedDict
import openpyxl
from six import text_type
from warnings import warn
import traceback
import datetime
import pytz

# The "pylint: disable" lines exist to ignore warnings about the imports we expect not to work not working

if sys.version > '3':
    from csv import DictReader
else:
    from unicodecsv import DictReader  # pylint: disable=F0401

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


def merge(base, mergee):
    for key, value in mergee.items():
        if key in base:
            if isinstance(value, TemporaryDict):
                for temporarydict_key, temporarydict_value in value.items():
                    if temporarydict_key in base[key]:
                        merge(base[key][temporarydict_key], temporarydict_value)
                    else:
                        base[key][temporarydict_key] = temporarydict_value
                for temporarydict_value in  value.items_no_keyfield:
                    base[key].items_no_keyfield.append(temporarydict_value)
            elif isinstance(value, dict) and isinstance(base[key], dict):
                merge(base[key], value)
            elif base[key] != mergee[key]:
                warn('Conflict between main sheet and sub sheet') # FIXME make this more useful (we used to say which subsheet broke...)
        else:
            base[key] = value

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
                yield { title_lookup.lookup_header(k):v for k,v in d.items() }
            else:
                yield d

    def __init__(self, input_name='', main_sheet_name='', timezone_name='UTC', root_id='ocid', convert_titles=False):
        self.input_name = input_name
        self.main_sheet_name = main_sheet_name
        self.sub_sheet_names = []
        self.timezone = pytz.timezone(timezone_name)
        self.root_id = root_id
        self.convert_titles = convert_titles
        self.parser = None

    def get_main_sheet_lines(self):
        if self.convert_titles:
            return self.convert_dict_titles(self.get_sheet_lines(self.main_sheet_name))
        else:
            return self.get_sheet_lines(self.main_sheet_name)

    def get_sub_sheets_lines(self):
        for sub_sheet_name in self.sub_sheet_names:
            if self.convert_titles:
                yield sub_sheet_name, self.convert_dict_titles(self.get_sheet_lines(sub_sheet_name),
                    self.parser.sub_sheets[sub_sheet_name].title_lookup if sub_sheet_name in self.parser.sub_sheets else None)
            else:
                yield sub_sheet_name, self.get_sheet_lines(sub_sheet_name)

    def get_sheet_lines(self, sheet_name):
        raise NotImplementedError

    def read_sheets(self):
        raise NotImplementedError


    def convert_types(self, in_dict):
        out_dict = OrderedDict()
        for key, value in in_dict.items():
            parts = key.split(':')
            if len(parts) > 1:
                out_dict[parts[0]] = convert_type(parts[1], value, self.timezone)
            else:
                out_dict[parts[0]] = convert_type('', value, self.timezone)
        return out_dict


    def unflatten(self):
        main_sheet_by_ocid = OrderedDict()
        # Eventually we should get rid of the concept of a "main sheet entirely"
        for sheet_name, lines in [(self.main_sheet_name, self.get_main_sheet_lines())] + list(self.get_sub_sheets_lines()):
            for line in lines:
                if all(x == '' for x in line.values()):
                    continue
                root_id_or_none = line[self.root_id] if self.root_id else None
                unflattened = unflatten_main_with_parser(self.parser, line, self.timezone)
                if root_id_or_none not in main_sheet_by_ocid:
                    main_sheet_by_ocid[root_id_or_none] = TemporaryDict('id')
                if 'id' in unflattened and unflattened['id'] in main_sheet_by_ocid[root_id_or_none]:
                    merge(main_sheet_by_ocid[root_id_or_none][unflattened.get('id')], unflattened)
                else:
                    main_sheet_by_ocid[root_id_or_none].append(unflattened)

        temporarydicts_to_lists(main_sheet_by_ocid)

        return sum(main_sheet_by_ocid.values(), [])


class CSVInput(SpreadsheetInput):
    encoding = 'utf-8'

    def read_sheets(self):
        sheet_file_names = os.listdir(self.input_name)
        if self.main_sheet_name+'.csv' not in sheet_file_names:
            raise ValueError('Main sheet "{}.csv" not found.'.format(self.main_sheet_name))
        sheet_file_names.remove(self.main_sheet_name+'.csv')

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

        self.sheet_names_map = {sheet_name: sheet_name for sheet_name in self.workbook.get_sheet_names()}
        # allow main sheet to be any case
        for sheet_name in list(self.sheet_names_map):
            if sheet_name.lower() == self.main_sheet_name.lower():
                self.sheet_names_map.pop(sheet_name)
                self.sheet_names_map[self.main_sheet_name] = sheet_name

        sheet_names = list(self.sheet_names_map.keys())
        if self.main_sheet_name not in sheet_names:
            raise ValueError('Main sheet "{}" not found in workbook.'.format(self.main_sheet_name))
        sheet_names.remove(self.main_sheet_name)
        self.sub_sheet_names = sheet_names

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
    for path, value in line.items():
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
    def __init__(self, keyfield, top_sheet=False):
        self.keyfield = keyfield
        self.items_no_keyfield = []
        self.data = OrderedDict()
        self.top_sheet = top_sheet

    def __repr__(self):
        return 'TemporaryDict(keyfield={}, items_no_keyfield={}, data={})'.format(repr(self.keyfield), repr(self.items_no_keyfield), repr(self.data))

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

