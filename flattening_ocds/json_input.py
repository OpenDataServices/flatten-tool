"""

This file contains code that takes an OCDS JSON release ifle as input (not a
JSON schema, for that see schema.py).

"""

import json
import six
from collections import OrderedDict
from decimal import Decimal
from flattening_ocds.schema import SchemaParser

BASIC_TYPES = [six.text_type, bool, int, Decimal]

class JSONParser(object):
    # Named for consistency with schema.SchemaParser, but not sure it's the most appropriate name.
    # Similarily with methods like parse_json_dict

    def __init__(self, json_filename=None, root_json_dict=None, main_sheet_name='main'):
        self.sub_sheets = {}
        self.main_sheet = []
        self.sub_sheet_lines = {}
        self.main_sheet_lines = []
        self.main_sheet_name = main_sheet_name

        if json_filename is None and root_json_dict is None:
            raise ValueError('Etiher json_filename or root_json_dict must be supplied')

        if json_filename is not None and root_json_dict is not None:
            raise ValueError('Only one of json_file or root_json_dict should be supplied')
 
        if json_filename:
            with open(json_filename) as json_file:
                self.root_json_dict = json.load(json_file, object_pairs_hook=OrderedDict, parse_float=Decimal)
        else:
            self.root_json_dict = root_json_dict

    def parse(self):
        root_json_list = self.root_json_dict # TODO add support for finding
        # the main json_list within the root_json_dict (e.g. root_json_dict['releases'])
        for json_dict in root_json_list:
            self.parse_json_dict(json_dict, sheet=self.main_sheet, sheet_lines=self.main_sheet_lines)
    
    def parse_json_dict(self, json_dict, sheet, sheet_lines, parent_name='', flattened_dict=None):
        # Possibly main_sheet should be main_sheet_columns, but this is
        # currently named for consistency with schema.py
        
        if flattened_dict is None:
            flattened_dict = {}
            top = True
        else:
            top = False

        for key, value in json_dict.items():
            if type(value) in BASIC_TYPES:
                if not key in sheet:
                    sheet.append(parent_name+key)
                flattened_dict[parent_name+key] = value
            elif hasattr(value, 'items'):
                self.parse_json_dict(
                    value,
                    sheet=sheet,
                    sheet_lines=sheet_lines,
                    parent_name=parent_name+key+'/',
                    flattened_dict=flattened_dict)
            elif hasattr(value, '__iter__'):
                if key not in self.sub_sheets:
                    self.sub_sheets[key] = []
                    self.sub_sheet_lines[key] = []
                for json_dict in value:
                    self.parse_json_dict(
                        json_dict,
                        sheet=self.sub_sheets[key],
                        sheet_lines=self.sub_sheet_lines[key])
            else:
                raise ValueError('Unsupported type {}'.format(type(value)))

        if top:
            sheet_lines.append(flattened_dict)
