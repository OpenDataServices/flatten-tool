"""

This file contains code that takes an OCDS JSON release ifle as input (not a
JSON schema, for that see schema.py).

"""

import json
import six
import copy
from collections import OrderedDict
from decimal import Decimal
from flattentool.schema import SchemaParser
from flattentool.input import path_search
from flattentool.sheet import Sheet
from warnings import warn

BASIC_TYPES = [six.text_type, bool, int, Decimal, type(None)]


class BadlyFormedJSONError(ValueError):
    pass


def sheet_key_field(sheet, key, id_key=None):
    """
    Check for a key in the sheet, and return it with any suffix (following a ':') that might be present).
    
    If a key does not exist, it will be created.

    """
    if id_key:
        if key in sheet: # If the key exists without a suffix, use that
            return key
        elif sheet.name == id_key: # also use without a suffix if the suffix matches the sheet name
            sheet.append(key)
            return key
        else: # else use it with the :id_key suffix
            if not key+':'+id_key in sheet:
                sheet.append(key+':'+id_key)
            return key+':'+id_key
    else:
        keys = [x for x in sheet if x.split(':')[0] == key]
        if not keys:
            sheet.append(key)
            return key
        elif len(keys) > 1:
            # This shouldn't ever happen, as the schema parser shouldn't output sheets like this...
            raise ValueError('Sheet contains two conflicting keys')
        else:
            return keys[0]

def sheet_key_title(sheet, key, id_key=None):
    """
    If the key has a corresponding title, return that. If doesn't, create it in the sheet and return it.

    """
    if id_key: # call sheet_key_field instead
        return sheet_key_field(sheet, key, id_key)
    title_lookup = {v: k for k, v in sheet.titles.items()}
    if key in title_lookup:
        return title_lookup[key]
    else:
        sheet.append(key)
        return key


class JSONParser(object):
    # Named for consistency with schema.SchemaParser, but not sure it's the most appropriate name.
    # Similarily with methods like parse_json_dict

    def __init__(self, json_filename=None, root_json_dict=None, main_sheet_name='main', schema_parser=None, root_list_path=None, root_id='ocid', use_titles=False):
        self.sub_sheets = {}
        self.main_sheet = Sheet()
        self.main_sheet_name = main_sheet_name
        self.root_list_path = root_list_path
        self.root_id = root_id
        self.use_titles = use_titles
        if schema_parser:
            self.sub_sheet_mapping = {'/'.join(k.split('/')[1:]): v for k,v in schema_parser.sub_sheet_mapping.items()}
            self.main_sheet = schema_parser.main_sheet
            self.sub_sheets = schema_parser.sub_sheets
            # Rollup is pulled from the schema_parser, as rollup is only possible if a schema parser is specified
            self.rollup = schema_parser.rollup
            self.schema_parser = schema_parser
        else:
            self.sub_sheet_mapping = {}
            self.rollup = False

        if json_filename is None and root_json_dict is None:
            raise ValueError('Etiher json_filename or root_json_dict must be supplied')

        if json_filename is not None and root_json_dict is not None:
            raise ValueError('Only one of json_file or root_json_dict should be supplied')
 
        if json_filename:
            with open(json_filename) as json_file:
                try:
                    self.root_json_dict = json.load(json_file, object_pairs_hook=OrderedDict, parse_float=Decimal)
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
            self.parse_json_dict(json_dict, sheet=self.main_sheet)
    
    def parse_json_dict(self, json_dict, sheet, json_key=None, id_extra_parent_name='', parent_name='', flattened_dict=None, parent_id_fields=None):
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

        if parent_name == '':
            # Only add the IDs for the top level of object in an array
            for k, v in parent_id_fields.items():
                flattened_dict[sheet_key(sheet, k, id_key=json_key)] = v

        if self.root_id and self.root_id in json_dict:
            parent_id_fields[self.root_id] = json_dict[self.root_id]

        if 'id' in json_dict:
            parent_id_fields[self.main_sheet_name+'/'+id_extra_parent_name+parent_name+'id'] = json_dict['id']


        for key, value in json_dict.items():
            if type(value) in BASIC_TYPES:
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
                    flattened_dict[sheet_key(sheet, parent_name+key)] = ';'.join(value)
                else:
                    if self.rollup and parent_name == '': # Rollup only currently possible to main sheet
                        if len(value) == 1:
                            for k, v in value[0].items():
                                if parent_name+key+'[]/'+k in self.schema_parser.main_sheet:
                                    if type(v) in BASIC_TYPES:
                                        flattened_dict[sheet_key(sheet, parent_name+key+'[]/'+k)] = v
                                    else:
                                        raise ValueError('Rolled up values must be basic types')
                        elif len(value) > 1:
                            for k in set(sum((list(x.keys()) for x in value), [])):
                                warn('More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'.format(parent_name+key))
                                if parent_name+key+'[]/'+k in self.schema_parser.main_sheet:
                                    flattened_dict[sheet_key(sheet, parent_name+key+'[]/'+k)] = 'WARNING: More than one value supplied, consult the relevant sub-sheet for the data.'

                    sub_sheet_name = self.sub_sheet_mapping[key] if key in self.sub_sheet_mapping else key
                    if sub_sheet_name not in self.sub_sheets:
                        self.sub_sheets[sub_sheet_name] = Sheet(name=sub_sheet_name)


                    for json_dict in value:
                        self.parse_json_dict(
                            json_dict,
                            sheet=self.sub_sheets[sub_sheet_name],
                            json_key=key,
                            parent_id_fields=parent_id_fields,
                            id_extra_parent_name=parent_name+key+'[]/')
            else:
                raise ValueError('Unsupported type {}'.format(type(value)))
        
        if top:
            sheet.lines.append(flattened_dict)
