from __future__ import unicode_literals
from flattening_ocds.json_input import JSONParser
from flattening_ocds.schema import SchemaParser
import pytest
from collections import OrderedDict

def test_jsonparser_exceptions(tmpdir):
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


def test_json_filename_ordered(tmpdir):
    test_json = tmpdir.join('test.json')
    test_json.write('{"a":"b", "c": "d"}')
    parser = JSONParser(json_filename=test_json.strpath)
    assert list(parser.root_json_dict.items()) == [('a','b'), ('c','d')]


def test_parse_empty_json_dict():
    parser = JSONParser(root_json_dict={})
    parser.parse()
    assert parser.main_sheet == []
    assert parser.main_sheet_lines == []
    assert parser.sub_sheets == {}
    assert parser.sub_sheet_lines == {}


def test_parse_basic_json_dict():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('a', 'b'),
        ('c', 'd'),
    ])])
    parser.parse()
    assert parser.main_sheet == [ 'a', 'c' ]
    assert parser.main_sheet_lines == [
        {'a': 'b', 'c': 'd'}
    ]
    assert parser.sub_sheets == {}
    assert parser.sub_sheet_lines == {}


def test_parse_nested_dict_json_dict():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('a', 'b'),
        ('c', OrderedDict([('d', 'e')])),
    ])])
    parser.parse()
    assert parser.main_sheet == [ 'a', 'c/d' ]
    assert parser.main_sheet_lines == [
        {'a': 'b', 'c/d': 'e'}
    ]
    assert parser.sub_sheets == {}
    assert parser.sub_sheet_lines == {}


def test_parse_nested_list_json_dict():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('a', 'b'),
        ('c', [OrderedDict([('d', 'e')])]),
    ])])
    parser.parse()
    assert parser.main_sheet == [ 'a' ]
    assert parser.main_sheet_lines == [
        {'a': 'b'}
    ]
    assert parser.sub_sheets == {'c':['d']}
    assert parser.sub_sheet_lines == {'c':[{'d':'e'}]}


def test_parse_using_schema(tmpdir):
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
    assert parser.main_sheet == [ 'a' ]
    assert parser.main_sheet_lines == [
        {'a': 'b'}
    ]
    assert len(parser.sub_sheets) == 1
    assert list(parser.sub_sheets['testB']) == list(['ocid', 'd', 'f'])
    assert parser.sub_sheet_lines == {'testB':[{'d':'e'}]}



def test_parse_ids():
    parser = JSONParser(root_json_dict=[OrderedDict([
        ('ocid', 1),
        ('id', 2),
        ('a', 'b'),
        ('c', [OrderedDict([('d', 'e')])]),
    ])])
    parser.parse()
    assert parser.main_sheet == [ 'ocid', 'id', 'a' ]
    assert parser.main_sheet_lines == [
        {
            'ocid': 1,
            'id': 2,
            'a': 'b'
        }
    ]
    assert parser.sub_sheets == {'c':['ocid','main/id','d']}
    assert parser.sub_sheet_lines == {'c':[{
        'ocid': 1,
        'main/id': 2,
        'd':'e'
    }]}

def test_root_list_path():
    parser = JSONParser(
        root_json_dict={'custom_key': [OrderedDict([
            ('a', 'b'),
            ('c', 'd'),
        ])]},
        root_list_path='custom_key')
    parser.parse()
    assert parser.main_sheet == [ 'a', 'c' ]
    assert parser.main_sheet_lines == [
        {'a': 'b', 'c': 'd'}
    ]
    assert parser.sub_sheets == {}
    assert parser.sub_sheet_lines == {}

# TODO Check support for decimals, integers, booleans
