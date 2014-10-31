import pytest
from schema import SchemaParser


def test_filename_and_dict_error(tmpdir):
    """A value error should be raised if both schema_filename and
    root_schema_dict are supplied to SchemaParser"""
    tmpfile = tmpdir.join('test_schema.json')
    tmpfile.write('{}')
    with pytest.raises(ValueError):
        SchemaParser(schema_filename=tmpfile.strpath, root_schema_dict={})


def test_references_followed(tmpdir):
    """JSON references should be followed when a JSON file is read."""
    tmpfile = tmpdir.join('test_schema.json')
    tmpfile.write('{"a":{"$ref":"#/b"}, "b":"c"}')
    parser = SchemaParser(schema_filename=tmpfile.strpath)
    assert parser.root_schema_dict['a'] == 'c'


def test_order_preserved(tmpdir):
    """Order should be preserved when a JSON file is read."""
    tmpfile = tmpdir.join('test_schema.json')
    tmpfile.write('{"a":{}, "c":{}, "b":{}, "d":{}}')
    parser = SchemaParser(schema_filename=tmpfile.strpath)
    assert list(parser.root_schema_dict.keys()) == ['a', 'c', 'b', 'd']


def test_main_sheet_basic(tmpdir):
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'testA': {},
            'testB': {}
        }
    })
    parser.parse()
    assert set(parser.main_sheet) == set(['testA', 'testB'])


def test_main_sheet_nested(tmpdir):
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'testA': {
                'type': 'object',
                'properties': { 'testC': {} }
            }
        }
    })
    parser.parse()
    assert set(parser.main_sheet) == set(['testA.testC'])


def test_sub_sheet(tmpdir):
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'testA': {
                'type': 'array',
                'items': {
                    'properties': { 'testB': {} }
                }
            },
        }
    })
    parser.parse()
    assert set(parser.main_sheet) == set(['testA'])
    assert parser.sub_sheets == {'testA':['ocid', 'testB']}
