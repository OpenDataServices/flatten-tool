# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flattentool.json_input import JSONParser, BadlyFormedJSONError
from flattentool.schema import SchemaParser
import pytest
from collections import OrderedDict
from six import text_type


def listify(d):
    return {k:list(v) for k,v in d.items()}


def test_jsonparser_bad_json(tmpdir):
    test_json = tmpdir.join('test.json')
    test_json.write('{"a":"b",}')
    with pytest.raises(BadlyFormedJSONError):
        JSONParser(json_filename=test_json.strpath)
    # JSONInputValueError also matches against ValueError
    with pytest.raises(ValueError):
        JSONParser(json_filename=test_json.strpath)


def test_jsonparser_arguments_exceptions(tmpdir):
    """
    Test that JSONParser throws a ValueError if it recievs too many or too few arguments.

    """
    test_json = tmpdir.join('test.json')
    test_json.write('{}')
    with pytest.raises(ValueError):
        JSONParser()
    with pytest.raises(ValueError):
        JSONParser(json_filename=test_json.strpath, root_json_dict={})


def test_json_filename(tmpdir):
    test_json = tmpdir.join('test.json')
    test_json.write('{"a":"b"}')
    parser = JSONParser(json_filename=test_json.strpath)
    assert parser.root_json_dict == {'a':'b'}


def test_json_filename_utf8(tmpdir):
    test_json = tmpdir.join('test.json')
    test_json.write_text('{"a":"éαГ😼𝒞人"}', encoding='utf-8')
    parser = JSONParser(json_filename=test_json.strpath)
    assert parser.root_json_dict == {'a':'éαГ😼𝒞人'}


def test_json_filename_ordered(tmpdir):
    test_json = tmpdir.join('test.json')
    test_json.write('{"a":"b", "c": "d"}')
    parser = JSONParser(json_filename=test_json.strpath)
    assert list(parser.root_json_dict.items()) == [('a','b'), ('c','d')]


def test_parse_empty_json_dict():
    parser = JSONParser(root_json_dict={})
    parser.parse()
    assert list(parser.main_sheet) == []
    assert parser.main_sheet.lines == []
    assert parser.sub_sheets == {}


def test_parse_basic_json_dict():
    parser = JSONParser(root_json_dict=[
        OrderedDict([
            ('a', 'b'),
            ('c', 'd'),
        ]),
        OrderedDict([
            ('a', 'e'),
            ('c', 'f'),
        ]),
    ])
    parser.parse()
    assert list(parser.main_sheet) == [ 'a', 'c' ]
    assert parser.main_sheet.lines == [
        {'a': 'b', 'c': 'd'},
        {'a': 'e', 'c': 'f'},
    ]
    assert parser.sub_sheets == {}


def test_parse_nested_dict_json_dict():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('a', 'b'),
        ('c', OrderedDict([('d', 'e')])),
    ])])
    parser.parse()
    assert list(parser.main_sheet) == [ 'a', 'c/d' ]
    assert parser.main_sheet.lines == [
        {'a': 'b', 'c/d': 'e'}
    ]
    assert parser.sub_sheets == {}


def test_parse_nested_list_json_dict():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('a', 'b'),
        ('c', [OrderedDict([('d', 'e')])]),
    ])])
    parser.parse()
    assert list(parser.main_sheet) == [ 'a' ]
    assert parser.main_sheet.lines == [
        {'a': 'b'}
    ]
    listify(parser.sub_sheets) == {'c': ['d']}
    parser.sub_sheets['c'].lines == [{'d':'e'}]


def test_parse_array():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('testarray', ['item','anotheritem'])
    ])])
    parser.parse()
    assert list(parser.main_sheet) == [ 'testarray' ]
    assert parser.main_sheet.lines == [
        {
            'testarray': 'item;anotheritem'
        }
    ]
    assert parser.sub_sheets == {}


def test_root_list_path():
    parser = JSONParser(
        root_json_dict={'custom_key': [OrderedDict([
            ('a', 'b'),
            ('c', 'd'),
        ])]},
        root_list_path='custom_key')
    parser.parse()
    assert list(parser.main_sheet) == [ 'a', 'c' ]
    assert parser.main_sheet.lines == [
        {'a': 'b', 'c': 'd'}
    ]
    assert parser.sub_sheets == {}


class TestParseIDs(object):
    def test_parse_ids(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('ocid', 1),
            ('id', 2),
            ('a', 'b'),
            ('c', [OrderedDict([('id', 3), ('d', 'e')]), OrderedDict([('id', 3), ('d', 'e2')])]),
            ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
        ])])
        parser.parse()
        assert list(parser.main_sheet) == [ 'ocid', 'id', 'a', 'f/g' ]
        assert parser.main_sheet.lines == [
            {
                'ocid': 1,
                'id': 2,
                'a': 'b',
                'f/g': 'h'
            }
        ]
        listify(parser.sub_sheets) == {'c': ['ocid','id','c/0/id','c/0/d']}
        assert parser.sub_sheets['c'].lines == [
            {
                'ocid': 1,
                'id': 2,
                'c/0/id': 3,
                'c/0/d':'e'
            },
            {
                'ocid': 1,
                'id': 2,
                'c/0/id': 3,
                'c/0/d':'e2'
            },
        ]

    def test_parse_ids_subsheet(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('ocid', 1),
            ('id', 2),
            ('testnest', [
                OrderedDict([
                    ('id', 3),
                    ('a', 'b'),
                    ('c', [OrderedDict([('d', 'e')]), OrderedDict([('d', 'e2')])]),
                    ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
                ])
            ])
        ])])
        parser.parse()
        assert list(parser.main_sheet) == [ 'ocid', 'id' ]
        assert parser.main_sheet.lines == [
            {
                'ocid': 1,
                'id': 2,
            }
        ]
        assert listify(parser.sub_sheets) == {
                'testnest': ['ocid', 'id', 'testnest/0/id', 'testnest/0/a', 'testnest/0/f/g'],
                'c': ['ocid', 'id', 'testnest/0/id', 'testnest/0/c/0/d']
            }
        assert parser.sub_sheets['testnest'].lines == [
                {
                    'ocid': 1,
                    'id': 2,
                    'testnest/0/id': 3,
                    'testnest/0/a': 'b',
                    'testnest/0/f/g': 'h',
                },
            ]
        assert parser.sub_sheets['c'].lines == [
            {
                'ocid': 1,
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/c/0/d':'e'
            },
            {
                'ocid': 1,
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/c/0/d':'e2'
            },
        ]

    def test_parse_ids_nested(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('ocid', 1),
            ('id', 2),
            ('a', 'b'),
            ('testnest', OrderedDict([
                ('id', 3),
                ('c', [OrderedDict([('d', 'e')]), OrderedDict([('d', 'e2')])])
            ])),
            ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
        ])])
        parser.parse()
        assert list(parser.main_sheet) == [ 'ocid', 'id', 'a', 'testnest/id', 'f/g' ]
        assert parser.main_sheet.lines == [
            {
                'ocid': 1,
                'id': 2,
                'a': 'b',
                'testnest/id': 3,
                'f/g': 'h'
            }
        ]
        assert listify(parser.sub_sheets) == {'c': ['ocid','id','testnest/id','testnest/c/0/d']}
        assert parser.sub_sheets['c'].lines == [
            {
                'ocid': 1,
                'id': 2,
                'testnest/id': 3,
                'testnest/c/0/d':'e'
            },
            {
                'ocid': 1,
                'id': 2,
                'testnest/id': 3,
                'testnest/c/0/d':'e2'
            },
        ]


class TestParseUsingSchema(object):
    def test_sub_sheet_names(self, tmpdir):
        test_schema = tmpdir.join('test.json')
        test_schema.write('''{
            "properties": {
                "c": {
                    "type": "array",
                    "items": {"$ref": "#/testB"}
                }
            },
            "testB": {
                "type": "object",
                "properties": {
                    "d": { "type": "string" },
                    "f": { "type": "string" }
                }
            }
        }''')
        schema_parser = SchemaParser(
            schema_filename=test_schema.strpath
        )
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[OrderedDict([
                ('a', 'b'),
                ('c', [OrderedDict([('d', 'e')])]),
            ])],
            schema_parser=schema_parser
        )
        parser.parse()
        assert list(parser.main_sheet) == [ 'a' ]
        assert parser.main_sheet.lines == [
            {'a': 'b'}
        ]
        assert len(parser.sub_sheets) == 1
        assert list(parser.sub_sheets['c']) == list(['ocid', 'c/0/d', 'c/0/f'])
        assert parser.sub_sheets['c'].lines == [{'c/0/d':'e'}]

    def test_column_matching(self, tmpdir): 
        test_schema = tmpdir.join('test.json')
        test_schema.write('''{
            "properties": {
                "c": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }''')
        schema_parser = SchemaParser(
            schema_filename=test_schema.strpath
        )
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[OrderedDict([
                ('c', ['d']),
            ])],
            schema_parser=schema_parser
        )
        parser.parse()
        assert list(parser.main_sheet) == [ 'c' ]
        assert parser.main_sheet.lines == [
                {'c': 'd'}
        ]
        assert len(parser.sub_sheets) == 0

    def test_rollup(self):
        schema_parser = SchemaParser(root_schema_dict={
            'properties': {
                'testA': {
                    'type': 'array',
                    'rollUp': [ 'testB' ],
                    'items': {
                        'type': 'object',
                        'properties': {
                            'testB': {'type': 'string'},
                            'testC': {'type': 'string'}
                        }
                    }
                },
            }
        }, rollup=True)
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[OrderedDict([
                ('testA', [OrderedDict([('testB', '1'), ('testC', '2')])]),
            ])],
            schema_parser=schema_parser
        )
        parser.parse()
        assert list(parser.main_sheet) == [ 'testA/0/testB' ]
        assert parser.main_sheet.lines == [
            {'testA/0/testB': '1'}
        ]
        assert len(parser.sub_sheets) == 1
        assert set(parser.sub_sheets['testA']) == set(['ocid', 'testA/0/testB', 'testA/0/testC'])
        assert parser.sub_sheets['testA'].lines == [{'testA/0/testB':'1', 'testA/0/testC': '2'}]

    def test_rollup_multiple_values(self, recwarn):
        schema_parser = SchemaParser(root_schema_dict={
            'properties': {
                'testA': {
                    'type': 'array',
                    'rollUp': [ 'testB' ],
                    'items': {
                        'type': 'object',
                        'properties': {
                            'testB': {'type': 'string'},
                            'testC': {'type': 'string'}
                        }
                    }
                },
            }
        }, rollup=True)
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[OrderedDict([
                ('testA', [
                    OrderedDict([('testB', '1'), ('testC', '2')]),
                    OrderedDict([('testB', '3'), ('testC', '4')])
                    ]),
            ])],
            schema_parser=schema_parser
        )
        parser.parse()
        assert list(parser.main_sheet) == [ 'testA/0/testB' ]
        assert parser.main_sheet.lines == [
            {
                'testA/0/testB': 'WARNING: More than one value supplied, consult the relevant sub-sheet for the data.'
            }
        ]
        assert len(parser.sub_sheets) == 1
        assert set(parser.sub_sheets['testA']) == set(['ocid', 'testA/0/testB', 'testA/0/testC'])
        assert parser.sub_sheets['testA'].lines == [
            {'testA/0/testB':'1', 'testA/0/testC': '2'},
            {'testA/0/testB':'3', 'testA/0/testC': '4'}
            ]
        w = recwarn.pop(UserWarning)
        assert 'Could not provide rollup' in text_type(w.message)

# TODO Check support for decimals, integers, booleans and Nones

class TestParseIDsCustomRootID(object):
    def test_parse_ids(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('custom', 1),
            ('id', 2),
            ('a', 'b'),
            ('c', [OrderedDict([('id', 3), ('d', 'e')]), OrderedDict([('id', 3), ('d', 'e2')])]),
            ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
        ])], root_id='custom')
        parser.parse()
        assert list(parser.main_sheet) == [ 'custom', 'id', 'a', 'f/g' ]
        assert parser.main_sheet.lines == [
            {
                'custom': 1,
                'id': 2,
                'a': 'b',
                'f/g': 'h'
            }
        ]
        assert listify(parser.sub_sheets) == {'c': ['custom','id','c/0/id','c/0/d']}
        assert parser.sub_sheets['c'].lines == [
            {
                'custom': 1,
                'id': 2,
                'c/0/id': 3,
                'c/0/d':'e'
            },
            {
                'custom': 1,
                'id': 2,
                'c/0/id': 3,
                'c/0/d':'e2'
            },
        ]

    def test_parse_ids_subsheet(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('custom', 1),
            ('id', 2),
            ('testnest', [
                OrderedDict([
                    ('id', 3),
                    ('a', 'b'),
                    ('c', [OrderedDict([('d', 'e')]), OrderedDict([('d', 'e2')])]),
                    ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
                ])
            ])
        ])], root_id='custom')
        parser.parse()
        assert list(parser.main_sheet) == [ 'custom', 'id' ]
        assert parser.main_sheet.lines == [
            {
                'custom': 1,
                'id': 2,
            }
        ]
        assert listify(parser.sub_sheets) == {
                'testnest': ['custom', 'id', 'testnest/0/id', 'testnest/0/a', 'testnest/0/f/g'],
                'c': ['custom', 'id', 'testnest/0/id', 'testnest/0/c/0/d']
            }
        assert parser.sub_sheets['testnest'].lines == [
            {
                'custom': 1,
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/a': 'b',
                'testnest/0/f/g': 'h',
            },
        ]
        assert parser.sub_sheets['c'].lines == [
            {
                'custom': 1,
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/c/0/d':'e'
            },
            {
                'custom': 1,
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/c/0/d':'e2'
            },
        ]

    def test_parse_ids_nested(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('custom', 1),
            ('id', 2),
            ('a', 'b'),
            ('testnest', OrderedDict([
                ('id', 3),
                ('c', [OrderedDict([('d', 'e')]), OrderedDict([('d', 'e2')])])
            ])),
            ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
        ])], root_id='custom')
        parser.parse()
        assert list(parser.main_sheet) == [ 'custom', 'id', 'a', 'testnest/id', 'f/g' ]
        assert parser.main_sheet.lines == [
            {
                'custom': 1,
                'id': 2,
                'a': 'b',
                'testnest/id': 3,
                'f/g': 'h'
            }
        ]
        assert listify(parser.sub_sheets) == {'c': ['custom','id','testnest/id','testnest/c/0/d']}
        assert parser.sub_sheets['c'].lines == [
            {
                'custom': 1,
                'id': 2,
                'testnest/id': 3,
                'testnest/c/0/d':'e'
            },
            {
                'custom': 1,
                'id': 2,
                'testnest/id': 3,
                'testnest/c/0/d':'e2'
            },
        ]


class TestParseIDsNoRootID(object):
    def test_parse_ids(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('id', 2),
            ('a', 'b'),
            ('c', [OrderedDict([('id', 3), ('d', 'e')]), OrderedDict([('id', 3), ('d', 'e2')])]),
            ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
        ])], root_id='')
        parser.parse()
        assert list(parser.main_sheet) == [ 'id', 'a', 'f/g' ]
        assert parser.main_sheet.lines == [
            {
                'id': 2,
                'a': 'b',
                'f/g': 'h'
            }
        ]
        assert listify(parser.sub_sheets) == {'c': ['id','c/0/id','c/0/d']}
        assert parser.sub_sheets['c'].lines == [
            {
                'id': 2,
                'c/0/id': 3,
                'c/0/d':'e'
            },
            {
                'id': 2,
                'c/0/id': 3,
                'c/0/d':'e2'
            },
        ]

    def test_parse_ids_subsheet(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('id', 2),
            ('testnest', [
                OrderedDict([
                    ('id', 3),
                    ('a', 'b'),
                    ('c', [OrderedDict([('d', 'e')]), OrderedDict([('d', 'e2')])]),
                    ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
                ])
            ])
        ])], root_id='')
        parser.parse()
        assert list(parser.main_sheet) == [ 'id' ]
        assert parser.main_sheet.lines == [
            {
                'id': 2,
            }
        ]
        assert listify(parser.sub_sheets) == {
                'testnest': ['id', 'testnest/0/id', 'testnest/0/a', 'testnest/0/f/g'],
                'c': ['id', 'testnest/0/id', 'testnest/0/c/0/d']
            }
        assert parser.sub_sheets['testnest'].lines ==  [
            {
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/a': 'b',
                'testnest/0/f/g': 'h',
            },
        ]
        assert parser.sub_sheets['c'].lines == [
            {
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/c/0/d':'e'
            },
            {
                'id': 2,
                'testnest/0/id': 3,
                'testnest/0/c/0/d':'e2'
            },
        ]

    def test_parse_ids_nested(self):
        parser = JSONParser(root_json_dict=[OrderedDict([
            ('id', 2),
            ('a', 'b'),
            ('testnest', OrderedDict([
                ('id', 3),
                ('c', [OrderedDict([('d', 'e')]), OrderedDict([('d', 'e2')])])
            ])),
            ('f', {'g':'h'}) # Check that having nested objects doesn't break ID output
        ])], root_id='')
        parser.parse()
        assert list(parser.main_sheet) == [ 'id', 'a', 'testnest/id', 'f/g' ]
        assert parser.main_sheet.lines == [
            {
                'id': 2,
                'a': 'b',
                'testnest/id': 3,
                'f/g': 'h'
            }
        ]
        assert listify(parser.sub_sheets) == {'c': ['id','testnest/id','testnest/c/0/d']}
        assert parser.sub_sheets['c'].lines == [
            {
                'id': 2,
                'testnest/id': 3,
                'testnest/c/0/d':'e'
            },
            {
                'id': 2,
                'testnest/id': 3,
                'testnest/c/0/d':'e2'
            },
        ]
