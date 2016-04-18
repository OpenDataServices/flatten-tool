import pytest
from collections import OrderedDict
from six import text_type
from flattentool.schema import SchemaParser, get_property_type_set
from flattentool.sheet import Sheet


type_string = {'type': 'string'}


def test_sub_sheet_list_like():
    # SubSheet object should be appendable and iterable...
    # .append() is used in json_input.py at https://github.com/OpenDataServices/flatten-tool/blob/master/flattentool/json_input.py#L33
    sub_sheet = Sheet()
    assert list(sub_sheet) == []
    sub_sheet.append('a')
    sub_sheet.append('b')
    assert list(sub_sheet) == ['a', 'b']
    # ... but also has an add_field method, which also appends
    sub_sheet.add_field('c')
    assert list(sub_sheet) == ['a', 'b', 'c']
    # but with the option to add an id_field, which appears at the start of the list
    sub_sheet.add_field('d', id_field=True)
    assert list(sub_sheet) == ['d', 'a', 'b', 'c']


def test_get_property_type_set():
    assert get_property_type_set({'type': 'a'}) == set(['a'])
    assert get_property_type_set({'type': ['a']}) == set(['a'])
    assert get_property_type_set({'type': ['a', 'b']}) == set(['a', 'b'])


def test_filename_and_dict_error(tmpdir):
    """A value error should be raised if both schema_filename and
    root_schema_dict are supplied to SchemaParser"""
    tmpfile = tmpdir.join('test_schema.json')
    tmpfile.write('{}')
    with pytest.raises(ValueError):
        SchemaParser(schema_filename=tmpfile.strpath, root_schema_dict={})
    # Supplying neither should also raise a ValueError
    with pytest.raises(ValueError):
        SchemaParser()

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


def test_main_sheet_basic():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': type_string,
            'Btest': type_string
        }
    })
    parser.parse()
    assert set(parser.main_sheet) == set(['Atest', 'Btest'])


def test_main_sheet_nested():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'object',
                'properties': {'Ctest': type_string}
            }
        }
    })
    parser.parse()
    assert set(parser.main_sheet) == set(['Atest/Ctest'])


def test_sub_sheet():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {'Btest': type_string}
                }
            },
        }
    })
    parser.parse()
    assert set(parser.main_sheet) == set([])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['ocid', 'Atest/0/Btest']


def object_in_array_example_properties(parent_name, child_name):
    return {
        'id': type_string,
        parent_name: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {child_name: type_string}
            }
        }
    }


class TestSubSheetParentID(object):
    def test_parent_is_object(self):
        parser = SchemaParser(root_schema_dict={
            'properties': {
                'Atest': {
                    'type': 'object',
                    'properties': object_in_array_example_properties('Btest', 'Ctest')
                }
            }
        })
        parser.parse()
        assert set(parser.main_sheet) == set(['Atest/id'])
        assert set(parser.sub_sheets) == set(['Ate_Btest'])
        assert list(parser.sub_sheets['Ate_Btest']) == ['ocid', 'Atest/id', 'Atest/Btest/0/Ctest']

    def test_parent_is_array(self):
        parser = SchemaParser(root_schema_dict={
            'properties': {
                'Atest': {
                    'type': 'array',
                    'items': {'type': 'object', 'properties': object_in_array_example_properties('Btest', 'Ctest')}
                }
            }
        })
        parser.parse()
        assert set(parser.main_sheet) == set()
        assert set(parser.sub_sheets) == set(['Atest', 'Ate_Btest'])
        assert list(parser.sub_sheets['Atest']) == ['ocid', 'Atest/0/id']
        assert list(parser.sub_sheets['Ate_Btest']) == ['ocid', 'Atest/0/id', 'Atest/0/Btest/0/Ctest']

    def test_two_parents(self):
        parser = SchemaParser(root_schema_dict={
            'properties': OrderedDict([
                ('Atest', {
                    'type': 'array',
                    'items': {'type': 'object',
                              'properties': object_in_array_example_properties('Btest', 'Ctest')}
                }),
                ('Dtest', {
                    'type': 'array',
                    'items': {'type': 'object',
                              'properties': object_in_array_example_properties('Btest', 'Etest')}
                })
            ])
        })
        parser.parse()
        assert set(parser.main_sheet) == set()
        assert set(parser.sub_sheets) == set(['Atest', 'Dtest', 'Ate_Btest', 'Dte_Btest'])
        assert list(parser.sub_sheets['Atest']) == ['ocid', 'Atest/0/id']
        assert list(parser.sub_sheets['Dtest']) == ['ocid', 'Dtest/0/id']
        assert list(parser.sub_sheets['Ate_Btest']) == ['ocid', 'Atest/0/id', 'Atest/0/Btest/0/Ctest']
        assert list(parser.sub_sheets['Dte_Btest']) == ['ocid', 'Dtest/0/id', 'Dtest/0/Btest/0/Etest']

    def test_parent_is_object_nested(self):
        parser = SchemaParser(root_schema_dict={
            'properties': {
                'Atest': {
                    'type': 'object',
                    'properties': {
                        'Btest': {
                            'type': 'object',
                            'properties': object_in_array_example_properties('Btest', 'Ctest')
                        }
                    }
                }
            }
        })
        parser.parse()
        assert set(parser.main_sheet) == set(['Atest/Btest/id'])
        assert set(parser.sub_sheets) == set(['Ate_Bte_Btest'])
        assert list(parser.sub_sheets['Ate_Bte_Btest']) == ['ocid', 'Atest/Btest/id', 'Atest/Btest/Btest/0/Ctest']


class TestSubSheetMainID(object):
    def test_parent_is_object(self):
        parser = SchemaParser(root_schema_dict={
            'properties': {
                'id': type_string,
                'Atest': {
                    'type': 'object',
                    'properties': object_in_array_example_properties('Btest', 'Ctest')
                }
            }
        })
        parser.parse()
        assert set(parser.main_sheet) == set(['id', 'Atest/id'])
        assert set(parser.sub_sheets) == set(['Ate_Btest'])
        assert list(parser.sub_sheets['Ate_Btest']) == ['ocid', 'id', 'Atest/id', 'Atest/Btest/0/Ctest']

    def test_parent_is_array(self):
        parser = SchemaParser(root_schema_dict={
            'properties': {
                'id': type_string,
                'Atest': {
                    'type': 'array',
                    'items': {'type': 'object',
                              'properties': object_in_array_example_properties('Btest', 'Ctest')}
                }
            }
        })
        parser.parse()
        assert set(parser.main_sheet) == set(['id'])
        assert set(parser.sub_sheets) == set(['Atest', 'Ate_Btest'])
        assert list(parser.sub_sheets['Atest']) == ['ocid', 'id', 'Atest/0/id']
        assert list(parser.sub_sheets['Ate_Btest']) == ['ocid', 'id', 'Atest/0/id', 'Atest/0/Btest/0/Ctest']

    def test_two_parents(self):
        parser = SchemaParser(root_schema_dict={
            'properties': OrderedDict([
                ('id', type_string),
                ('Atest', {
                    'type': 'array',
                    'items': {'type': 'object',
                              'properties': object_in_array_example_properties('Btest', 'Ctest')}
                }),
                ('Dtest', {
                    'type': 'array',
                    'items': {'type': 'object',
                              'properties': object_in_array_example_properties('Btest', 'Etest')}
                })
            ])
        })
        parser.parse()
        assert set(parser.main_sheet) == set(['id'])
        assert set(parser.sub_sheets) == set(['Atest', 'Dtest', 'Ate_Btest', 'Dte_Btest'])
        assert list(parser.sub_sheets['Atest']) == ['ocid', 'id', 'Atest/0/id']
        assert list(parser.sub_sheets['Dtest']) == ['ocid', 'id', 'Dtest/0/id']
        assert list(parser.sub_sheets['Ate_Btest']) == ['ocid', 'id', 'Atest/0/id', 'Atest/0/Btest/0/Ctest']
        assert list(parser.sub_sheets['Dte_Btest']) == ['ocid', 'id', 'Dtest/0/id', 'Dtest/0/Btest/0/Etest']

    def test_custom_main_sheet_name(self):
        parser = SchemaParser(
            root_schema_dict={
                'properties': {
                    'id': type_string,
                    'Atest': {
                        'type': 'object',
                        'properties': object_in_array_example_properties('Btest', 'Ctest')
                    }
                }
            },
            main_sheet_name='custom_main_sheet_name'
        )
        parser.parse()
        assert set(parser.main_sheet) == set(['id', 'Atest/id'])
        assert set(parser.sub_sheets) == set(['Ate_Btest'])
        assert list(parser.sub_sheets['Ate_Btest']) == [
            'ocid',
            'id',
            'Atest/id',
            'Atest/Btest/0/Ctest']


def test_simple_array():
    parser = SchemaParser(
        root_schema_dict={
            'properties': {
                'Atest': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            }
        },
        main_sheet_name='custom_main_sheet_name'
    )
    parser.parse()
    assert set(parser.main_sheet) == set(['Atest'])


def test_nested_simple_array():
    parser = SchemaParser(
        root_schema_dict={
            'properties': {
                'Atest': {
                    'type': 'array',
                    'items': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        }
                    }
                }
            }
        },
        main_sheet_name='custom_main_sheet_name'
    )
    parser.parse()
    assert set(parser.main_sheet) == set(['Atest'])


def test_references_sheet_names(tmpdir):
    """
    The referenced name used to be used for the sheet name,
    but is NOT any more.

    """
    tmpfile = tmpdir.join('test_schema.json')
    tmpfile.write('''{
        "properties": { "Atest": {
            "type": "array",
            "items": {"$ref": "#/Btest"}
        } },
        "Btest": { "type": "object", "properties": {"Ctest":{"type": "string"}} }
    }''')
    parser = SchemaParser(schema_filename=tmpfile.strpath)
    parser.parse()
    assert set(parser.sub_sheets) == set(['Atest']) # used to be Btest
    assert list(parser.sub_sheets['Atest']) == ['ocid', 'Atest/0/Ctest']


def test_rollup():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'rollUp': [ 'Btest' ],
                'items': {
                    'type': 'object',
                    'properties': {
                        'Btest': type_string,
                        'Ctest': type_string
                    }
                }
            },
        }
    }, rollup=True)
    parser.parse()
    assert set(parser.main_sheet) == set(['Atest/0/Btest'])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert set(parser.sub_sheets['Atest']) == set(['ocid', 'Atest/0/Btest', 'Atest/0/Ctest'])


def test_bad_rollup(recwarn):
    '''
    When rollUp is specified, but the field is missing in the schema, we expect
    a warning.

    '''
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'rollUp': [ 'Btest' ],
                'items': {
                    'type': 'object',
                    'properties': {
                        'Ctest': type_string
                    }
                }
            },
        }
    }, rollup=True)
    parser.parse()

    w = recwarn.pop(UserWarning)
    assert 'Btest in rollUp but not in schema' in text_type(w.message)

    assert set(parser.main_sheet) == set()
    assert set(parser.sub_sheets) == set(['Atest'])
    assert set(parser.sub_sheets['Atest']) == set(['ocid', 'Atest/0/Ctest'])


def test_sub_sheet_custom_id():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {'Btest': type_string}
                }
            },
        }
    }, root_id='custom')
    parser.parse()
    assert set(parser.main_sheet) == set([])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['custom', 'Atest/0/Btest']

def test_sub_sheet_no_root_id():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {'Btest': type_string}
                }
            },
        }
    }, root_id='')
    parser.parse()
    assert set(parser.main_sheet) == set([])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['Atest/0/Btest']

def test_use_titles(recwarn):
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'title': 'ATitle',
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'Btest': {
                            'type': 'string',
                            'title': 'BTitle'
                        }
                    }
                }
            },
            'Ctest': {
                'type': 'string',
                'title': 'CTitle'
            }
        }
    }, use_titles=True)
    parser.parse()
    assert set(parser.main_sheet) == set(['CTitle'])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['ocid', 'ATitle:BTitle']

    # Array title missing
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'Btest': {
                            'type': 'string',
                            'title': 'BTitle'
                        }
                    }
                }
            },
            'Ctest': {
                'type': 'string',
                'title': 'CTitle'
            }
        }
    }, use_titles=True)
    parser.parse()
    assert set(parser.main_sheet) == set(['CTitle'])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['ocid']
    w = recwarn.pop(UserWarning)
    assert 'does not have a title' in text_type(w.message)

    # Main sheet title missing
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'title': 'ATitle',
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'Btest': {
                            'type': 'string',
                            'title': 'BTitle'
                        }
                    }
                }
            },
            'Ctest': {
                'type': 'string'
            }
        }
    }, use_titles=True)
    parser.parse()
    assert set(parser.main_sheet) == set([])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['ocid', 'ATitle:BTitle']
    w = recwarn.pop(UserWarning)
    assert 'does not have a title' in text_type(w.message)

    # Child sheet title missing
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'title': 'ATitle',
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'Btest': {
                            'type': 'string'
                        }
                    }
                }
            },
            'Ctest': {
                'type': 'string',
                'title': 'CTitle'
            }
        }
    }, use_titles=True)
    parser.parse()
    assert set(parser.main_sheet) == set(['CTitle'])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert list(parser.sub_sheets['Atest']) == ['ocid']
    w = recwarn.pop(UserWarning)
    assert 'does not have a title' in text_type(w.message)


def test_titles_rollup():
    parser = SchemaParser(root_schema_dict={
        'properties': {
            'Atest': {
                'type': 'array',
                'title': 'ATitle',
                'rollUp': [ 'Btest' ],
                'items': {
                    'type': 'object',
                    'properties': {
                        'Btest': {
                            'type': 'string',
                            'title': 'BTitle',
                        },
                        'Ctest': {
                            'type': 'string',
                            'title': 'CTitle',
                        }
                    }
                }
            },
        }
    }, rollup=True, use_titles=True)
    parser.parse()
    assert set(parser.main_sheet) == set(['ATitle:BTitle'])
    assert set(parser.sub_sheets) == set(['Atest'])
    assert set(parser.sub_sheets['Atest']) == set(['ocid', 'ATitle:BTitle', 'ATitle:CTitle'])


def test_schema_from_uri(httpserver):
    httpserver.serve_content('{"a":{"$ref":"#/b"}, "b":"c"}', 404)
    parser = SchemaParser(schema_filename=httpserver.url)
    assert parser.root_schema_dict['a'] == 'c'
