"""Classes for reading from a JSON schema"""

from __future__ import print_function
from collections import OrderedDict
import jsonref
from warnings import warn


class SubSheet(object):
    def __init__(self):
        self.id_columns = []
        self.columns = []

    def add_field(self, field, id_field=False):
        columns = self.id_columns if id_field else self.columns
        if field not in columns:
            columns.append(field)

    def __iter__(self):
        yield 'ocid'
        for column in self.id_columns:
            yield column
        for column in self.columns:
            yield column


class SchemaParser(object):
    """Parse the fields of a JSON schema into a flattened structure."""

    def __init__(self, schema_filename=None, root_schema_dict=None, main_sheet_name='main'):
        self.sub_sheets = {}
        self.main_sheet = []
        self.main_sheet_name = main_sheet_name

        if root_schema_dict is not None and schema_filename is not None:
            raise ValueError('Only one of schema_file or root_schema_dict should be supplied')
        if schema_filename:
            with open(schema_filename) as schema_file:
                self.root_schema_dict = jsonref.load(schema_file, object_pairs_hook=OrderedDict)
        else:
            self.root_schema_dict = root_schema_dict

    def parse(self):
        for field in self.parse_schema_dict(self.main_sheet_name, self.root_schema_dict):
            self.main_sheet.append(field)

    def parse_schema_dict(self, parent_name, schema_dict, parent_id_fields=None):
        parent_id_fields = parent_id_fields or []
        if 'properties' in schema_dict:
            if 'id' in schema_dict['properties']:
                id_fields = parent_id_fields + [parent_name+'/id']
            else:
                id_fields = parent_id_fields

            for property_name, property_schema_dict in schema_dict['properties'].items():
                property_type = property_schema_dict.get('type')
                if not isinstance(property_type, list):
                    property_type_set = set([property_type])
                else:
                    property_type_set = set(property_type)

                if 'object' in property_type_set:
                    for field in self.parse_schema_dict(parent_name+'/'+property_name, property_schema_dict,
                                                        parent_id_fields=id_fields):
                        yield property_name+'/'+field
                elif 'array' in property_type_set:
                    if hasattr(property_schema_dict['items'], '__reference__'):
                        sub_sheet_name = property_schema_dict['items'].__reference__['$ref'].split('/')[-1]
                    else:
                        sub_sheet_name = property_name

                    if sub_sheet_name not in self.sub_sheets:
                        self.sub_sheets[sub_sheet_name] = SubSheet()
                    sub_sheet = self.sub_sheets[sub_sheet_name]

                    for field in id_fields:
                        sub_sheet.add_field(field+':'+property_name, id_field=True)
                    for field in self.parse_schema_dict(parent_name+'/'+property_name+'[]',
                                                        property_schema_dict['items'],
                                                        parent_id_fields=id_fields):
                        sub_sheet.add_field(field)
                elif 'string' in property_type_set:
                    yield property_name
                elif 'number' in property_type_set:
                    yield property_name+':number'
                elif 'integer' in property_type_set:
                    yield property_name+':integer'
                elif 'boolean' in property_type_set:
                    yield property_name+':boolean'
                else:
                    warn('Unrecognised types {} for property "{}" with context "{}", so this property has been ignored.'.format(
                        repr(property_type_set), 
                        property_name,
                        parent_name))
        else:
            pass
            #print(parent_name)
