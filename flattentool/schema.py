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
        try:
            int(first_title)
            return first_title + '/' + self.lookup_header_list(remaining_titles)
        except ValueError:
            pass

        if first_title in self:
            if remaining_titles:
                return self[first_title].property_name + '/' + self[first_title].lookup_header_list(remaining_titles)
            else:
                return self[first_title].property_name
        else:
            # If we can't look up the title, treat it and any children as
            # field names directly.
            # Strip spaces off these.
            return '/'.join(x.strip(' ') for x in title_header_list)

    def __setitem__(self, key, value):
        self.data[key.replace(' ', '').lower()] = value

    def __getitem__(self, key):
        if key is None:
            raise KeyError
        else:
            return self.data[key.replace(' ', '').lower()]

    def __contains__(self, key):
        if key is None:
            return False
        else:
            return key.replace(' ', '').lower() in self.data


class SchemaParser(object):
    """Parse the fields of a JSON schema into a flattened structure."""

    def __init__(self, schema_filename=None, root_schema_dict=None, rollup=False, root_id=None, use_titles=False, create_reference_tables=False):
        self.sub_sheets = {}
        self.main_sheet = Sheet()
        self.sub_sheet_mapping = {}
        self.rollup = rollup
        self.root_id = root_id
        self.use_titles = use_titles
        self.title_lookup = TitleLookup()
        self.flattened = {}
        self.create_reference_tables = create_reference_tables
        if self.create_reference_tables:
            self.reference_tables = {}
            self.reference_table_headers = ['title','name','description','type','format','allowed_values','required']

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
        if self.create_reference_tables:
            self.reference_tables['main'] = []
        fields = self.parse_schema_dict('', self.root_schema_dict)
        for field, title, property_schema_dict in fields:
            if self.create_reference_tables:
                if 'format' in property_schema_dict:
                    type_ = property_schema_dict['format']
                else:
                    type_ = property_schema_dict['type']
                self.reference_tables['main'].append({
                    'title': title,
                    'name': field,
                    'description': property_schema_dict.get('description'),
                    'type': type_ if isinstance(type_, str) else ','.join(x for x in type_ if x != 'null'),
                    'format': '',
                    'allowed_values': '',
                    'required': 'True' if property_schema_dict['required_bool'] else 'False'
                })
            if self.use_titles:
                if not title:
                    warn('Field {} does not have a title, skipping.'.format(field))
                else:
                    self.main_sheet.append(title)
            else:
                self.main_sheet.append(field)

    def parse_schema_dict(self, parent_path, schema_dict, parent_id_fields=None, title_lookup=None, parent_title='', sub_sheet_name=None):
        if sub_sheet_name is None:
            sub_sheet_name = self.root_schema_dict
        if parent_path:
            parent_path = parent_path + '/'
        parent_id_fields = parent_id_fields or []
        title_lookup = self.title_lookup if title_lookup is None else title_lookup
        if 'properties' in schema_dict:
            if 'id' in schema_dict['properties']:
                if self.use_titles:
                    id_fields = parent_id_fields + [(parent_title if parent_title is not None else parent_path)+(schema_dict['properties']['id'].get('title') or 'id')]
                else:
                    id_fields = parent_id_fields + [parent_path+'id']
            else:
                id_fields = parent_id_fields

            for property_name, property_schema_dict in schema_dict['properties'].items():
                if self.create_reference_tables:
                    property_schema_dict['required_bool'] = property_name in schema_dict['required'] if 'required' in schema_dict else False
                property_type_set = get_property_type_set(property_schema_dict)

                title = property_schema_dict.get('title')
                if title:
                    title_lookup[title] = TitleLookup()
                    title_lookup[title].property_name = property_name

                if 'object' in property_type_set:
                    self.flattened[parent_path+property_name] = "object"
                    for field, child_title, child_property_schema_dict in self.parse_schema_dict(
                            parent_path+property_name,
                            property_schema_dict,
                            parent_id_fields=id_fields,
                            title_lookup=title_lookup.get(title),
                            parent_title=parent_title+title+':' if title else None,
                            sub_sheet_name=sub_sheet_name):
                        yield (
                            property_name+'/'+field,
                            # TODO ambiguous use of "title"
                            (title+':'+child_title if title and child_title else None),
                            child_property_schema_dict
                        )

                elif 'array' in property_type_set:
                    self.flattened[parent_path+property_name] = "array"
                    type_set = get_property_type_set(property_schema_dict['items'])
                    if 'string' in type_set:
                        self.flattened[parent_path+property_name] = "string_array"
                        yield property_name, title, property_schema_dict
                    elif 'array' in type_set:
                        self.flattened[parent_path+property_name] = "array_array"
                        if 'string' in get_property_type_set(property_schema_dict['items']['items']):
                            yield property_name, title, property_schema_dict
                        else:
                            raise ValueError
                    elif 'object' in type_set:
                        if title:
                            title_lookup[title].property_name = property_name

                        sub_sheet_name = ('_'.join(x[:3] for x in parent_path.split('/') if x != '0') + property_name)[:31]

                        #self.sub_sheet_mapping[parent_name+'/'+property_name] = sub_sheet_name

                        if sub_sheet_name not in self.sub_sheets:
                            self.sub_sheets[sub_sheet_name] = Sheet(root_id=self.root_id, name=sub_sheet_name)
                        sub_sheet = self.sub_sheets[sub_sheet_name]
                        sub_sheet.title_lookup = title_lookup.get(title)

                        for field in id_fields:
                            sub_sheet.add_field(field, id_field=True)
                        fields = self.parse_schema_dict(
                                parent_path+property_name+'/0',
                                property_schema_dict['items'],
                                parent_id_fields=id_fields,
                                title_lookup=title_lookup.get(title),
                                parent_title=parent_title+title+':' if title else None,
                                sub_sheet_name=sub_sheet_name)

                        rolledUp = set()

                        if self.create_reference_tables:
                            self.reference_tables[sub_sheet_name] = []

                        for field, child_title, child_property_schema_dict in fields:
                            if self.create_reference_tables:
                                if 'format' in child_property_schema_dict:
                                    type_ = child_property_schema_dict['format']
                                else:
                                    type_ = child_property_schema_dict['type']
                                self.reference_tables[sub_sheet_name].append({
                                    'title': parent_title+title+':'+child_title if title is not None and child_title is not None else '',
                                    'name': parent_path+property_name+'/0/'+field,
                                    'description': child_property_schema_dict['description'],
                                    'type': type_ if isinstance(type_, str) else ','.join(x for x in type_ if x != 'null'),
                                    'format': '',
                                    'allowed_values': '',
                                    'required': 'True' if child_property_schema_dict['required_bool'] else 'False'
                                })
                            if self.use_titles:
                                if not child_title:
                                    warn('Field {} does not have a title, skipping.'.format(field))
                                elif not title:
                                    warn('Field {} does not have a title, skipping it and all its children.'.format(property_name))
                                else:
                                    # This code only works for arrays that are at 0 or 1 layer of nesting
                                    sub_sheet.add_field(parent_title+title+':'+child_title)
                            else:
                                sub_sheet.add_field(parent_path+property_name+'/0/'+field)
                            if self.rollup and 'rollUp' in property_schema_dict and field in property_schema_dict['rollUp']:
                                rolledUp.add(field)
                                yield property_name+'/0/'+field, (title+':'+child_title if title and child_title else None), child_property_schema_dict

                        # Check that all items in rollUp are in the schema
                        if self.rollup and 'rollUp' in property_schema_dict:
                            missedRollUp = set(property_schema_dict['rollUp']) - rolledUp
                            if missedRollUp:
                                warn('{} in rollUp but not in schema'.format(', '.join(missedRollUp)))
                    else:
                        raise ValueError
                elif 'string' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "string"
                    yield property_name, title, property_schema_dict
                elif 'number' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "number"
                    yield property_name, title, property_schema_dict
                elif 'integer' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "integer"
                    yield property_name, title, property_schema_dict
                elif 'boolean' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "boolean"
                    yield property_name, title, property_schema_dict
                else:
                    warn('Unrecognised types {} for property "{}" with context "{}",'
                         'so this property has been ignored.'.format(
                             repr(property_type_set),
                             property_name,
                             parent_path))
        else:
            warn('Skipping field "{}", because it has no properties.'.format(parent_path))
