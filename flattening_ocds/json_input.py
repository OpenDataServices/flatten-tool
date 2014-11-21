"""

This file contains code that takes an OCDS JSON release ifle as input (not a
JSON schema, for that see schema.py).

"""

import json
import six
from collections import OrderedDict
from decimal import Decimal

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

    
    def parse_json_dict(self):
        # Possibly main_sheet should be main_sheet_columns, but this is
        # currently named for consistency with schema.py

        root_json_list = self.root_json_dict # TODO add support for finding
        # the main json_list withint the root_json_dict (e.g. root_json_dict['releases'])
        for json_dict in root_json_list:
            for key, value in json_dict.items():
                if type(value) in BASIC_TYPES and not key in self.main_sheet:
                    self.main_sheet.append(key)
            self.main_sheet_lines.append({k:v for k,v in json_dict.items() if type(v) in BASIC_TYPES})
