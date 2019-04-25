"""

This file contains code that takes an instace of a JSON file as input (not a
JSON schema, for that see schema.py).

"""

import csv
import json
import six
import copy
from collections import OrderedDict
from decimal import Decimal
from flattentool.schema import SchemaParser, make_sub_sheet_name
from flattentool.input import path_search
from flattentool.sheet import Sheet
from warnings import warn
import codecs
import xmltodict

BASIC_TYPES = [six.text_type, bool, int, Decimal, type(None)]


class BadlyFormedJSONError(ValueError):
    pass


class BadlyFormedJSONErrorUTF8(BadlyFormedJSONError):
    pass


def sheet_key_field(sheet, key):
    if key not in sheet:
        sheet.append(key)
    return key

def sheet_key_title(sheet, key):
    """
    If the key has a corresponding title, return that. If doesn't, create it in the sheet and return it.

    """
    if key in sheet.titles:
        title = sheet.titles[key]
        if title not in sheet:
            sheet.append(title)
        return title
    else:
        if key not in sheet:
            sheet.append(key)
        return key


def lists_of_dicts_paths(xml_dict):
    for key, value in xml_dict.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            yield (key,)
            for x in value:
                if isinstance(x, dict):
                    for path in lists_of_dicts_paths(x):
                        yield (key,) + path
        elif isinstance(value, dict):
            for path in lists_of_dicts_paths(value):
                yield (key,) + path


def dicts_to_list_of_dicts(lists_of_dicts_paths_set, xml_dict, path=()):
    for key, value in xml_dict.items():
        if isinstance(value, list):
            for x in value:
                if isinstance(x, dict):
                    dicts_to_list_of_dicts(lists_of_dicts_paths_set, x, path+(key,))
        elif isinstance(value, dict):
            child_path = path+(key,)
            dicts_to_list_of_dicts(lists_of_dicts_paths_set, value, child_path)
            if child_path in lists_of_dicts_paths_set:
                xml_dict[key] = [value]


def list_dict_consistency(xml_dict):
    '''
        For use with XML files opened with xmltodict.

        If there is only one tag, xmltodict produces a dict. If there are
        multiple, xmltodict produces a list of dicts. This functions replaces
        dicts with lists of dicts, if there exists a list of dicts for the same
        path elsewhere in the file.
    '''
    lists_of_dicts_paths_set = set(lists_of_dicts_paths(xml_dict))
    dicts_to_list_of_dicts(lists_of_dicts_paths_set, xml_dict)


class JSONParser(object):
    # Named for consistency with schema.SchemaParser, but not sure it's the most appropriate name.
    # Similarily with methods like parse_json_dict

    def __init__(self, json_filename=None, root_json_dict=None, schema_parser=None, root_list_path=None,
                 root_id='ocid', use_titles=False, xml=False, id_name='id', filter_field=None, filter_value=None,
                 preserve_fields=None, remove_empty_schema_columns=False, truncation_length=3):
        self.sub_sheets = {}
        self.main_sheet = Sheet()
        self.root_list_path = root_list_path
        self.root_id = root_id
        self.use_titles = use_titles
        self.truncation_length = truncation_length
        self.id_name = id_name
        self.xml = xml
        self.filter_field = filter_field
        self.filter_value = filter_value
        self.remove_empty_schema_columns = remove_empty_schema_columns
        if schema_parser:
            self.main_sheet = copy.deepcopy(schema_parser.main_sheet)
            self.sub_sheets = copy.deepcopy(schema_parser.sub_sheets)
            if remove_empty_schema_columns:
                # Don't use columns from the schema parser
                # (avoids empty columns)
                self.main_sheet.columns = []
                for sheet_name, sheet in list(self.sub_sheets.items()):
                    sheet.columns = []
            # Rollup is pulled from the schema_parser, as rollup is only possible if a schema parser is specified
            self.rollup = schema_parser.rollup
            self.schema_parser = schema_parser
        else:
            self.rollup = False

        if preserve_fields:
            # Extract fields to be preserved from input CSV file (uses every row)
            preserve_fields_list = []
            with open(preserve_fields, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                for row in csvreader:
                    preserve_fields_list = preserve_fields_list + row
            self.preserve_fields = preserve_fields_list
        else:
            self.preserve_fields = None


        if self.xml:
            with codecs.open(json_filename, 'rb') as xml_file:
                top_dict = xmltodict.parse(
                    xml_file,
                    force_list=(root_list_path,),
                    force_cdata=True,
                    )
                # AFAICT, this should be true for *all* XML files
                assert len(top_dict) == 1
                root_json_dict = list(top_dict.values())[0]
                list_dict_consistency(root_json_dict)
            json_filename = None

        if json_filename is None and root_json_dict is None:
            raise ValueError('Etiher json_filename or root_json_dict must be supplied')

        if json_filename is not None and root_json_dict is not None:
            raise ValueError('Only one of json_file or root_json_dict should be supplied')

        if json_filename:
            with codecs.open(json_filename, encoding='utf-8') as json_file:
                try:
                    self.root_json_dict = json.load(json_file, object_pairs_hook=OrderedDict, parse_float=Decimal)
                except UnicodeError as err:
                    raise BadlyFormedJSONErrorUTF8(*err.args)
                except ValueError as err:
                    raise BadlyFormedJSONError(*err.args)
        else:
            self.root_json_dict = root_json_dict

    def parse(self):
        if self.root_list_path is None:
            root_json_list = self.root_json_dict
        else:
            root_json_list = path_search(self.root_json_dict, self.root_list_path.split('/'))
        for json_dict in root_json_list:
            if json_dict is None:
                # This is particularly useful for IATI XML, in order to not
                # fallover on empty activity, e.g. <iati-activity/>
                continue
            self.parse_json_dict(json_dict, sheet=self.main_sheet)

        if self.remove_empty_schema_columns:
            # Remove sheets with no lines of data
            for sheet_name, sheet in list(self.sub_sheets.items()):
                if not sheet.lines:
                    del self.sub_sheets[sheet_name]

    def parse_json_dict(self, json_dict, sheet, json_key=None, parent_name='', flattened_dict=None, parent_id_fields=None, top_level_of_sub_sheet=False):
        """
        Parse a json dictionary.

        json_dict - the json dictionary
        sheet - a sheet.Sheet object representing the resulting spreadsheet
        json_key - the key that maps to this JSON dict, either directly to the dict, or to a dict that this list contains.  Is None if this dict is contained in root_json_list directly.
        """
        # Possibly main_sheet should be main_sheet_columns, but this is
        # currently named for consistency with schema.py

        if self.use_titles:
            sheet_key = sheet_key_title
        else:
            sheet_key = sheet_key_field

        parent_id_fields = copy.copy(parent_id_fields) or OrderedDict()
        if flattened_dict is None:
            flattened_dict = {}
            top = True
        else:
            top = False

        if parent_name == '' and self.filter_field and self.filter_value:
            if self.filter_field not in json_dict:
                return
            if json_dict[self.filter_field] != self.filter_value:
                return

        if top_level_of_sub_sheet:
            # Only add the IDs for the top level of object in an array
            for k, v in parent_id_fields.items():
                if self.xml:
                    flattened_dict[sheet_key(sheet, k)] = v['#text']
                else:
                    flattened_dict[sheet_key(sheet, k)] = v

        if self.root_id and self.root_id in json_dict:
            parent_id_fields[sheet_key(sheet, self.root_id)] = json_dict[self.root_id]

        if self.id_name in json_dict:
            parent_id_fields[sheet_key(sheet, parent_name+self.id_name)] = json_dict[self.id_name]


        for key, value in json_dict.items():
            if self.preserve_fields and key not in self.preserve_fields:
                continue
            if type(value) in BASIC_TYPES:
                if self.xml and key == '#text':
                    # Handle the text output from xmltodict
                    key = ''
                    parent_name = parent_name.strip('/')
                flattened_dict[sheet_key(sheet, parent_name+key)] = value
            elif hasattr(value, 'items'):
                self.parse_json_dict(
                    value,
                    sheet=sheet,
                    json_key=key,
                    parent_name=parent_name+key+'/',
                    flattened_dict=flattened_dict,
                    parent_id_fields=parent_id_fields)
            elif hasattr(value, '__iter__'):
                if all(type(x) in BASIC_TYPES for x in value):
                    # Check for an array of BASIC types
                    # TODO Make this check the schema
                    # TODO Error if the any of the values contain the seperator
                    # TODO Support doubly nested arrays
                    flattened_dict[sheet_key(sheet, parent_name+key)] = ';'.join(map(six.text_type, value))
                else:
                    if self.rollup and parent_name == '': # Rollup only currently possible to main sheet
                        if len(value) == 1:
                            for k, v in value[0].items():
                                if self.use_titles and parent_name+key+'/0/'+k in self.schema_parser.main_sheet.titles:
                                    if type(v) in BASIC_TYPES:
                                        flattened_dict[sheet_key_title(sheet, parent_name+key+'/0/'+k)] = v
                                    else:
                                        raise ValueError('Rolled up values must be basic types')
                                elif not self.use_titles and parent_name+key+'/0/'+k in self.schema_parser.main_sheet:
                                    if type(v) in BASIC_TYPES:
                                        flattened_dict[sheet_key(sheet, parent_name+key+'/0/'+k)] = v
                                    else:
                                        raise ValueError('Rolled up values must be basic types')
                        elif len(value) > 1:
                            for k in set(sum((list(x.keys()) for x in value), [])):
                                warn('More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'.format(parent_name+key))
                                if parent_name+key+'/0/'+k in self.schema_parser.main_sheet:
                                    flattened_dict[sheet_key(sheet, parent_name+key+'/0/'+k)] = 'WARNING: More than one value supplied, consult the relevant sub-sheet for the data.'

                    sub_sheet_name = make_sub_sheet_name(parent_name, key, truncation_length=self.truncation_length)
                    if sub_sheet_name not in self.sub_sheets:
                        self.sub_sheets[sub_sheet_name] = Sheet(name=sub_sheet_name)

                    for json_dict in value:
                        if json_dict is None:
                            continue
                        self.parse_json_dict(
                            json_dict,
                            sheet=self.sub_sheets[sub_sheet_name],
                            json_key=key,
                            parent_id_fields=parent_id_fields,
                            parent_name=parent_name+key+'/0/',
                            top_level_of_sub_sheet=True)
            else:
                raise ValueError('Unsupported type {}'.format(type(value)))

        if top:
            sheet.lines.append(flattened_dict)
