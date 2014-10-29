"""Classes for reading from a JSON schema"""

from __future__ import print_function
from collections import OrderedDict
import jsonref


class SchemaParser(object):
    """Parse the fields of a JSON schema into a flattened structure."""

    def __init__(self, schema_filename=None, root_schema_dict=None):
        self.sub_sheets = {}
        self.main_sheet = []

        if root_schema_dict and schema_filename:
            raise ValueError('Only one of schema_file or root_schema_dict should be supplied')
        if schema_filename:
            with open(schema_filename) as schema_file:
                self.root_schema_dict = jsonref.load(schema_file, object_pairs_hook=OrderedDict)
        else:
            self.root_schema_dict = root_schema_dict

    def parse(self):
        for field in self.parse_schema_dict(self.root_schema_dict):
            self.main_sheet.append(field)

    def parse_schema_dict(self, schema_dict):
        if 'properties' in schema_dict:
            for property_name, property_schema_dict in schema_dict['properties'].items():
                if property_schema_dict.get('type') == 'object':
                    for field in self.parse_schema_dict(property_schema_dict):
                        yield property_name+'.'+field
                elif property_schema_dict.get('type') == 'array':
                    yield property_name
                    if property_name not in self.sub_sheets:
                        self.sub_sheets[property_name] = ['ocid']
                    for field in self.parse_schema_dict(property_schema_dict['items']):
                        if field not in self.sub_sheets[property_name]:
                            self.sub_sheets[property_name].append(field)
                else:
                    yield property_name
