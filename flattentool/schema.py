"""Classes for reading from a JSON schema"""

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from six.moves import UserDict
from six import text_type
import jsonref
from warnings import warn
from flattentool.sheet import Sheet
import codecs

def get_property_type_set(property_schema_dict):
    property_type = property_schema_dict.get('type', [])
    if not isinstance(property_type, list):
        return set([property_type])
    else:
        return set(property_type)


def make_sub_sheet_name(parent_path, property_name):
    return ('_'.join(x[:3] for x in parent_path.split('/') if x != '0') + property_name)[:31]



class TitleLookup(UserDict):
    property_name = None

    def lookup_header(self, title_header):
        if type(title_header) == text_type:
            return self.lookup_header_list(title_header.split(':'))
        else:
            return title_header

    def lookup_header_list(self, title_header_list):
        first_title = title_header_list[0]
        remaining_titles = title_header_list[1:]
        try:
            int(first_title)
            return first_title + ('/' + self.lookup_header_list(remaining_titles) if remaining_titles else '')
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

    def __init__(self, schema_filename=None, root_schema_dict=None, rollup=False, root_id=None, use_titles=False):
        self.sub_sheets = {}
        self.main_sheet = Sheet()
        self.sub_sheet_mapping = {}
        self.rollup = rollup
        self.root_id = root_id
        self.use_titles = use_titles
        self.title_lookup = TitleLookup()
        self.flattened = {}

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
        fields = self.parse_schema_dict('', self.root_schema_dict)
        for field, title in fields:
            if self.use_titles:
                if not title:
                    warn('Field {} does not have a title, skipping.'.format(field))
                else:
                    self.main_sheet.append(title)
            else:
                self.main_sheet.append(field)

    def parse_schema_dict(self, parent_path, schema_dict, parent_id_fields=None, title_lookup=None, parent_title=''):
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
                property_type_set = get_property_type_set(property_schema_dict)

                title = property_schema_dict.get('title')
                if title:
                    title_lookup[title] = TitleLookup()
                    title_lookup[title].property_name = property_name

                if 'object' in property_type_set:
                    self.flattened[parent_path+property_name] = "object"
                    for field, child_title in self.parse_schema_dict(
                            parent_path+property_name,
                            property_schema_dict,
                            parent_id_fields=id_fields,
                            title_lookup=title_lookup.get(title),
                            parent_title=parent_title+title+':' if parent_title is not None and title else None):
                        yield (
                            property_name+'/'+field,
                            # TODO ambiguous use of "title"
                            (title+':'+child_title if title and child_title else None)
                        )

                elif 'array' in property_type_set:
                    flattened_key = parent_path.replace('/0/', '/')+property_name
                    self.flattened[flattened_key] = "array"
                    type_set = get_property_type_set(property_schema_dict['items'])
                    if 'string' in type_set or not type_set:
                        self.flattened[flattened_key] = "string_array"
                        yield property_name, title
                    elif 'number' in type_set:
                        self.flattened[flattened_key] = "number_array"
                        yield property_name, title
                    elif 'array' in type_set:
                        self.flattened[flattened_key] = "array_array"
                        nested_type_set = get_property_type_set(property_schema_dict['items']['items'])
                        if 'string' in nested_type_set or 'number' in nested_type_set:
                            yield property_name, title
                        else:
                            raise ValueError
                    elif 'object' in type_set:
                        if title:
                            title_lookup[title].property_name = property_name

                        sub_sheet_name = make_sub_sheet_name(parent_path, property_name) 
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
                                parent_title=parent_title+title+':' if parent_title is not None and title else None)

                        rolledUp = set()

                        for field, child_title in fields:
                            if self.use_titles:
                                if not child_title or parent_title is None:
                                    warn('Field {}{}/0/{} is missing a title, skipping.'.format(parent_path, property_name, field))
                                elif not title:
                                    warn('Field {}{} does not have a title, skipping it and all its children.'.format(parent_path, property_name))
                                else:
                                    # This code only works for arrays that are at 0 or 1 layer of nesting
                                    sub_sheet.add_field(parent_title+title+':'+child_title)
                            else:
                                sub_sheet.add_field(parent_path+property_name+'/0/'+field)
                            if self.rollup and 'rollUp' in property_schema_dict and field in property_schema_dict['rollUp']:
                                rolledUp.add(field)
                                yield property_name+'/0/'+field, (title+':'+child_title if title and child_title else None)

                        # Check that all items in rollUp are in the schema
                        if self.rollup and 'rollUp' in property_schema_dict:
                            missedRollUp = set(property_schema_dict['rollUp']) - rolledUp
                            if missedRollUp:
                                warn('{} in rollUp but not in schema'.format(', '.join(missedRollUp)))
                    else:
                        raise ValueError
                elif 'string' in property_type_set or not property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "string"
                    yield property_name, title
                elif 'number' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "number"
                    yield property_name, title
                elif 'integer' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "integer"
                    yield property_name, title
                elif 'boolean' in property_type_set:
                    self.flattened[parent_path.replace('/0/', '/')+property_name] = "boolean"
                    yield property_name, title
                else:
                    warn('Unrecognised types {} for property "{}" with context "{}",'
                         'so this property has been ignored.'.format(
                             repr(property_type_set),
                             property_name,
                             parent_path))
        else:
            warn('Skipping field "{}", because it has no properties.'.format(parent_path))
