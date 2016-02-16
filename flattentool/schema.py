"""Classes for reading from a JSON schema"""

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from six.moves import UserDict
import jsonref
from warnings import warn
from flattentool.sheet import Sheet
import codecs

def get_property_type_set(property_schema_dict):
    property_type = property_schema_dict.get('type')
    if not isinstance(property_type, list):
        return set([property_type])
    else:
        return set(property_type)


class TitleLookup(UserDict):
    property_name = None

    def lookup_header(self, title_header):
        return self.lookup_header_list(title_header.split(':'))

    def lookup_header_list(self, title_header_list):
        first_title = title_header_list[0]
        remaining_titles = title_header_list[1:]
        if first_title in self:
            if remaining_titles:
                return self[first_title].property_name + '/' + self[first_title].lookup_header_list(remaining_titles)
            else:
                return self[first_title].property_name
        else:
            return '/'.join(title_header_list)


class SchemaParser(object):
    """Parse the fields of a JSON schema into a flattened structure."""

    def __init__(self, schema_filename=None, root_schema_dict=None, main_sheet_name='main', rollup=False, root_id='ocid', use_titles=False):
        self.sub_sheets = {}
        self.main_sheet = Sheet()
        self.sub_sheet_mapping = {}
        self.main_sheet_name = main_sheet_name
        self.rollup = rollup
        self.root_id = root_id
        self.use_titles = use_titles
        self.title_lookup = TitleLookup()

        if root_schema_dict is None and schema_filename is  None:
            raise ValueError('One of schema_filename or root_schema_dict must be supplied')
        if root_schema_dict is not None and schema_filename is not None:
            raise ValueError('Only one of schema_filename or root_schema_dict should be supplied')
        if schema_filename:
            if schema_filename.startswith('http'):
                import requests
                r = requests.get(schema_filename)
                self.root_schema_dict = jsonref.loads(r.text, object_pairs_hook=OrderedDict)
            else:
                with codecs.open(schema_filename, encoding="utf-8") as schema_file:
                    self.root_schema_dict = jsonref.load(schema_file, object_pairs_hook=OrderedDict)
        else:
            self.root_schema_dict = root_schema_dict

    def parse(self):
        fields = self.parse_schema_dict(self.main_sheet_name, self.root_schema_dict)
        for field, title in fields:
            if self.use_titles:
                if not title:
                    warn('Field {} does not have a title, skipping.'.format(field))
                else:
                    self.main_sheet.append(title)
            else:
                self.main_sheet.append(field)

    def parse_schema_dict(self, parent_name, schema_dict, parent_id_fields=None, title_lookup=None):
        parent_id_fields = parent_id_fields or []
        title_lookup = self.title_lookup if title_lookup is None else title_lookup
        if 'properties' in schema_dict:
            if 'id' in schema_dict['properties']:
                id_fields = parent_id_fields + [parent_name+'/id']
            else:
                id_fields = parent_id_fields

            for property_name, property_schema_dict in schema_dict['properties'].items():
                property_type_set = get_property_type_set(property_schema_dict)

                title = property_schema_dict.get('title')
                title_lookup[title] = TitleLookup()
                title_lookup[title].property_name = property_name

                if 'object' in property_type_set:
                    for field, child_title in self.parse_schema_dict(
                            parent_name+'/'+property_name,
                            property_schema_dict,
                            parent_id_fields=id_fields,
                            title_lookup=title_lookup[title]):
                        yield (
                            property_name+'/'+field,
                            # TODO ambiguous use of "title"
                            (title+':'+child_title if title and child_title else None) 
                        )

                elif 'array' in property_type_set:
                    type_set = get_property_type_set(property_schema_dict['items'])
                    if 'string' in type_set:
                        yield property_name+':array', title
                    elif 'array' in type_set:
                        if 'string' in get_property_type_set(property_schema_dict['items']['items']):
                            yield property_name+':array', title
                        else:
                            raise ValueError
                    elif 'object' in type_set:
                        title_lookup[title].property_name = property_name+'[]'
                        if hasattr(property_schema_dict['items'], '__reference__'):
                            sub_sheet_name = property_schema_dict['items'].__reference__['$ref'].split('/')[-1]
                        else:
                            sub_sheet_name = property_name

                        self.sub_sheet_mapping[parent_name+'/'+property_name] = sub_sheet_name

                        if sub_sheet_name not in self.sub_sheets:
                            self.sub_sheets[sub_sheet_name] = Sheet(root_id=self.root_id, name=sub_sheet_name)
                        sub_sheet = self.sub_sheets[sub_sheet_name]

                        for field in id_fields:
                            sub_sheet.add_field(field+':'+property_name, id_field=True)
                        fields = self.parse_schema_dict(parent_name+'/'+property_name+'[]',
                                property_schema_dict['items'],
                                parent_id_fields=id_fields,
                                title_lookup=title_lookup[title])

                        rolledUp = set()

                        for field, child_title in fields:
                            if self.use_titles:
                                if not child_title:
                                    warn('Field {} does not have a title, skipping.'.format(field))
                                else:
                                    sub_sheet.add_field(child_title)
                            else:
                                sub_sheet.add_field(field)
                            if self.rollup and 'rollUp' in property_schema_dict and field in property_schema_dict['rollUp']:
                                rolledUp.add(field)
                                yield property_name+'[]/'+field, (title+':'+child_title if title and child_title else None)

                        # Check that all items in rollUp are in the schema
                        if self.rollup and 'rollUp' in property_schema_dict:
                            missedRollUp = set(property_schema_dict['rollUp']) - rolledUp
                            if missedRollUp:
                                warn('{} in rollUp but not in schema'.format(', '.join(missedRollUp)))
                    else:
                        raise ValueError
                elif 'string' in property_type_set:
                    yield property_name, title
                elif 'number' in property_type_set:
                    yield property_name+':number', title
                elif 'integer' in property_type_set:
                    yield property_name+':integer', title
                elif 'boolean' in property_type_set:
                    yield property_name+':boolean', title
                else:
                    warn('Unrecognised types {} for property "{}" with context "{}",'
                         'so this property has been ignored.'.format(
                             repr(property_type_set),
                             property_name,
                             parent_name))
        else:
            warn('Skipping field "{}", because it has no properties.'.format(parent_name))
