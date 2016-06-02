'''
The tests in these functions are the minimal cases necessary to give you a good
understanding of the expected behaviour of flattentool.

These tests aren't concerned with the loading and saving of the data or schema,
they are concenred with what flattentool does with those data and schema.

It is worth being aware that the syntax for specifying column headings is
modelled closely on the `path` that is returned in any errors from the Python
JSON Schema library.

There are two modes of operating:

1. Deduce the structure from the column headings written in a JSON-schema-like
   path format

2. Deduce the structure from a JSON schema and infer what the columns are by
   comparing the column headings with the titles used in the schema structure


Throughout these tests there are a few things we do to make sure we're testing
properly:

* The titles are named differently from the propery names (by adding " Title"
  to the name)

* We put differing spacing and capitalisation in the headings from what is used
  in titles to make sure that it is the headings that come trhough into the
  source maps, and not the schema titles

* When addresses are used as lists, the array type in the schema must have a
  title ("Address Title"), the title of the individual adresses ("Address Item
  Item") doesn't matter

To resolve the $ref entries in the schema, the whole schema is passed through
`jsonref`.

TODO: Extra columns
'''

from collections import OrderedDict
from decimal import Decimal
import warnings

from jsonref import JsonRef
import pytest

from flattentool.input import SpreadsheetInput, convert_type, WITH_CELLS
from flattentool.tests.test_init import original_cell_and_row_locations, original_headings
from flattentool.schema import SchemaParser


def test_type_conversion_no_schema():
    '''\
    Without a schema flattentool keeps integers as they are, but makes
    everything else a string.

    These examples show some different types and their outputs.

    QUESTION: Is this behaviour predictable? Should everything be treated
    as a string perhaps?
    '''
    sheets = [
        {
            'name': 'main',
            'headings': ['int', 'string', 'decimal', 'float'],
            'rows': [
                [1, 'a', Decimal('1.2'), 1.3],
                ['1', 'a', '1.2', '1.3'],
                ['InvalidInt', 1, 'InvalidDecimal', 'InvalidFloat'],
            ]
        }
    ]
    expected = [
        OrderedDict([('int', 1), ('string', 'a'), ('decimal', '1.2'),
                     ('float', '1.3')]),
        # Note how int is 1 the first time, and '1' the second, with
        # everything else unchanged.
        OrderedDict([('int', '1'), ('string', 'a'), ('decimal', '1.2'),
                     ('float', '1.3')]),
        OrderedDict([('int', 'InvalidInt'), ('string', 1),
                     ('decimal', 'InvalidDecimal'), ('float', 'InvalidFloat')])
    ]
    # TODO It would be nice to assert there are no warnings here, but py.test
    # doesn't seem to make this easy
    assert (expected, None, None) == run(sheets)


def test_type_conversion_with_schema():
    '''
    With a schema flattentool converts input to the correct types. It returns
    int, float and decimal as `Decimal` instances though because the underlying
    schema treats them all just as 'number'.
    '''
    sheets = [
        {
            'name': 'main',
            'headings': ['int', 'string', 'decimal', 'float'],
            'rows': [
                [1, 'a', Decimal('1.2'), 1.3],
                ['1', 'a', '1.2', '1.3'],
                ['InvalidInt', 1, 'InvalidDecimal', 'InvalidFloat'],
            ]
        }
    ]
    schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            'int': {'type': 'number'},
            'string': {'type': 'string'},
            'decimal': {'type': 'number'},
            'float': {'type': 'number'},
        },
    }
    expected = [
        OrderedDict([
            ('int', Decimal('1')),
            ('string', 'a'),
            ('decimal', Decimal('1.2')),
            ('float', Decimal(
                '1.3000000000000000444089209850062616169452667236328125'
            ))
        ]),
        # Notice how the decimal representation of the float isn't quite right
        # because of float errors. Probably better to put input in as strings
        # to avoid this issue.
        OrderedDict([
            ('int', Decimal('1')),
            ('string', 'a'),
            ('decimal', Decimal('1.2')),
            ('float', Decimal('1.3'))]),
        # Notice how the schema validator allows through invalid data, but
        # converts things to strings if it can
        OrderedDict([
            ('int', 'InvalidInt'),
            ('string', '1'),
            ('decimal', 'InvalidDecimal'),
            ('float', 'InvalidFloat')]),
    ]
    with pytest.warns(UserWarning) as type_warnings:
        assert (expected, None, None) == run(sheets, schema)
    # check that only one warning was raised
    assert len(type_warnings) == 3
    # check that the message matches
    messages = [type_warning.message.args[0] for type_warning in type_warnings]
    assert messages == [
        'Non-numeric value "InvalidInt" found in number column, returning as string instead.',
        'Non-numeric value "InvalidDecimal" found in number column, returning as string instead.',
        'Non-numeric value "InvalidFloat" found in number column, returning as string instead.',
    ]


@pytest.mark.xfail
def test_merging_cols():
    '''
    This test demonstrates two problems:

    * Single rows are returned as a row, not as a list of rows with length 1
    * Columns with the same name result in the first being overwritten and
      not appearing in the cell source map
    '''
    sheets = [
        {
            'name': 'main',
            'headings': ['int', 'int'],
            'rows': [
                [1, 2],
            ]
        }
    ]
    # XXX We don't correctly get a list of lists here, just [OrderedDict([(u'int', 2)])]
    expected_result = [
        [OrderedDict([(u'int', 2)])]
    ]
    # XXX Fails to keep the source map to cell B2 because the value is lost early on in
    #     converting the row to a dictionary
    expected_cell_source_map = OrderedDict([
        (u'main/0/int', [('main', 'A', 2, 'int'), ('main', 'B', 2, 'int')]),
        (u'main/0', [('main', 2)]),
    ])
    expected_heading_source_map = OrderedDict([
        (u'main/int', [('main', 'int')]),
    ])
    expected = (expected_result, expected_cell_source_map, expected_heading_source_map)
    assert expected == run(sheets, source_maps=True)


test_dict_data_result = [
    OrderedDict([('name', 'James'), ('address',  OrderedDict([('house', '15')]))]),
]

test_dict_data_sheets = [
    {
        'name': 'main',
        'headings': ['name', 'address/house'],
        'rows': [
            ['James', '15'],
        ],
    },
]

test_dict_data_cell_source_map = OrderedDict([
    ('main/0/address/house', [('main', 'B', 2, 'address/house')]),
    ('main/0/name', [('main', 'A', 2, 'name')]),
    ('main/0/address', [('main', 2)]),
    ('main/0', [('main', 2)]),
])

test_dict_data_heading_source_map = OrderedDict([
    ('main/address/house', [('main', 'address/house')]),
    ('main/name', [('main', 'name')]),
])

test_dict_data = [
    # No schema case
    (
        test_dict_data_sheets,
        None,
        test_dict_data_result,
        test_dict_data_cell_source_map,
        test_dict_data_heading_source_map,
    ),
    # Schema with no titles (same source maps as above)
    (
        test_dict_data_sheets,
        {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'definitions': {
                'Address': {
                    'type': 'object',
                    'properties': {
                        'house': {'type': 'string'},
                    },
                }
            },
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'address': {
                    '$ref': '#/definitions/Address'
                },
            },
        },
        test_dict_data_result,
        test_dict_data_cell_source_map,
        test_dict_data_heading_source_map,
    ),
    # Schema with titles that aren't used in the headings (same source maps as two cases above)
    (
        test_dict_data_sheets,
        {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'title': 'Person Title',
            'definitions': {
                'Address': {
                    'type': 'object',
                    'title': 'Address Title',
                    'properties': {
                        'house': {'type': 'string'},
                    },
                }
            },
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'address': {
                    '$ref': '#/definitions/Address'
                }
            },
        },
        test_dict_data_result,
        test_dict_data_cell_source_map,
        test_dict_data_heading_source_map,
    ),
    # Schema with titles used in the headings (different source maps)
    (
        [
            {
                'name': 'main',
                'headings': [' NAmE TiTLe ', ' ADDresS TiTLe : HOusE TiTLe '],
                'rows': [
                    ['James', '15'],
                ],
            },
        ],
        {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'title': 'Person Title',
            'definitions': {
                'Address': {
                    'type': 'object',
                    'title': 'Address Title',
                    'properties': {
                        'house': {
                            'type': 'string',
                            'title': 'House Title',
                        },
                    },
                }
            },
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'title': 'Name Title',
                },
                'address': {
                    '$ref': '#/definitions/Address'
                },
            },
        },
        [
            OrderedDict([('name', 'James'), ('address',  OrderedDict([('house', '15')]))]),
        ],
        OrderedDict([
            ('main/0/address/house', [('main', 'B', 2, ' ADDresS TiTLe : HOusE TiTLe ')]),
            ('main/0/name', [('main', 'A', 2, ' NAmE TiTLe ')]),
            ('main/0/address', [('main', 2)]),
            ('main/0', [('main', 2)]),
        ]),
        OrderedDict([
            ('main/address/house', [('main', ' ADDresS TiTLe : HOusE TiTLe ')]),
            ('main/name', [('main', ' NAmE TiTLe ')]),
        ]),
    )
]


@pytest.mark.parametrize(
    'sheets, schema, expected_result, expected_cell_source_map, expected_heading_source_map',
    test_dict_data
)
def test_dict(sheets, schema, expected_result, expected_cell_source_map, expected_heading_source_map):
    result, cell_source_map, heading_source_map = run(sheets, schema=schema, source_maps=True)
    assert expected_result == result
    if WITH_CELLS:
        assert expected_cell_source_map == cell_source_map
        assert expected_heading_source_map == heading_source_map


test_list_of_dicts_data_result = [
     OrderedDict([
        ('name', 'James'),
        ('address',  [
            OrderedDict([
                ('house', '15'),
            ])
        ])])
]

test_list_of_dicts_data_sheets = [
    {
        'name': 'main',
        'headings': ['name', 'address/0/house'],
        'rows': [
            ['James', '15'],
        ],
    },
]

test_list_of_dicts_data_cell_source_map = OrderedDict([
    (u'main/0/address/0/house', [('main', 'B', 2, 'address/0/house')]),
    (u'main/0/name', [('main', 'A', 2, 'name')]),
    (u'main/0/address/0', [('main', 2)]),
    (u'main/0', [('main', 2)])
])

test_list_of_dicts_data_heading_source_map = OrderedDict([
    ('main/address/house', [('main', 'address/0/house')]),
    ('main/name', [('main', 'name')]),
])

test_list_of_dicts_data_schema_with_titles = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'title': 'Person Title',
    'definitions': {
        'Address': {
            'type': 'object',
            'title': 'Address Item Title',
            'properties': {
                'house': {
                    'type': 'string',
                    'title': 'House Title',
                },
            },
        },
    },
    'properties': {
        'name': {
            'type': 'string',
            'title': 'Name Title',
        },
        'address': {
            'items': {
                '$ref': '#/definitions/Address',
            },
            'type': 'array',
            'title': 'Address Title',
        },
    },
}

test_list_of_dicts_data = [
    # No schema case
    (
        test_list_of_dicts_data_sheets,
        None,
        test_list_of_dicts_data_result,
        test_list_of_dicts_data_cell_source_map,
        test_list_of_dicts_data_heading_source_map,
    ),
    # Schema with no titles (same source maps as above)
    (
        test_list_of_dicts_data_sheets,
        {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'definitions': {
                'Address': {
                    'type': 'object',
                    'title': 'Address Item Title',
                    'properties': {
                        'house': {
                            'type': 'string',
                        },
                    },
                },
            },
            'properties': {
                'name': {
                    'type': 'string',
                },
                'address': {
                    'items': {
                        '$ref': '#/definitions/Address',
                    },
                    'type': 'array',
                },
            },
        },
        test_list_of_dicts_data_result,
        test_list_of_dicts_data_cell_source_map,
        test_list_of_dicts_data_heading_source_map,
    ),
    # Schema with titles that aren't used in the headings (same source maps as two cases above)
    (
        test_list_of_dicts_data_sheets,
        test_list_of_dicts_data_schema_with_titles,
        test_list_of_dicts_data_result,
        test_list_of_dicts_data_cell_source_map,
        test_list_of_dicts_data_heading_source_map,
    ),
    # Schema with titles used in the headings (different source maps)
    (
        [
            {
                'name': 'main',
                'headings': [' NAmE TiTLe ', ' ADDresS TiTLe : 0 : HOusE TiTLe '],
                'rows': [
                    ['James', '15'],
                ],
            },
        ],
        test_list_of_dicts_data_schema_with_titles,
        test_list_of_dicts_data_result,
        OrderedDict([
            (u'main/0/address/0/house', [('main', 'B', 2, ' ADDresS TiTLe : 0 : HOusE TiTLe ')]),
            (u'main/0/name', [('main', 'A', 2, ' NAmE TiTLe ')]),
            (u'main/0/address/0', [('main', 2)]),
            (u'main/0', [('main', 2)])
        ]),
        OrderedDict([
            ('main/address/house', [('main', ' ADDresS TiTLe : 0 : HOusE TiTLe ')]),
            ('main/name', [('main', ' NAmE TiTLe ')]),
        ]),
    )
]


@pytest.mark.parametrize(
    'sheets, schema, expected_result, expected_cell_source_map, expected_heading_source_map',
    test_list_of_dicts_data
)
def test_list_of_dicts(sheets, schema, expected_result, expected_cell_source_map, expected_heading_source_map):
    result, cell_source_map, heading_source_map = run(sheets, schema=schema, source_maps=True)
    assert expected_result == result
    if WITH_CELLS:
        assert expected_cell_source_map == cell_source_map
        assert expected_heading_source_map == heading_source_map


test_list_of_dicts_with_ids_data_result = [
     OrderedDict([
        ('id', 'person1'),
        ('name', 'James'),
        ('address',  [
            OrderedDict([
                ('id', 'address1'),
                ('house', '15'),
            ])
        ])])
]

test_list_of_dicts_with_ids_data_sheets = [
    {
        'name': 'main',
        'headings': ['id', 'name', 'address/0/id', 'address/0/house'],
        'rows': [
            ['person1', 'James', 'address1', '15'],
        ],
    },
]

test_list_of_dicts_with_ids_data_cell_source_map = OrderedDict([
    (u'main/0/address/0/house', [('main', 'D', 2, 'address/0/house')]),
    (u'main/0/address/0/id', [('main', 'C', 2, 'address/0/id')]),
    (u'main/0/id', [('main', 'A', 2, 'id')]),
    (u'main/0/name', [('main', 'B', 2, 'name')]),
    (u'main/0/address/0', [('main', 2)]),
    (u'main/0', [('main', 2)])
])

test_list_of_dicts_with_ids_data_heading_source_map = OrderedDict([
    ('main/address/house', [('main', 'address/0/house')]),
    ('main/address/id', [('main', 'address/0/id')]),
    ('main/id', [('main', 'id')]),
    ('main/name', [('main', 'name')]),
])

test_list_of_dicts_with_ids_data_schema_with_titles = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'object',
    'title': 'Person Title',
    'definitions': {
        'Address': {
            'type': 'object',
            'title': 'Address Item Title',
            'properties': {
                'house': {
                    'type': 'string',
                    'title': 'House Title',
                },
                'id': {
                    'type': 'string',
                    'title': 'Identifier',
                },
            },
        },
    },
    'properties': {
        'id': {
            'type': 'string',
            'title': 'Identifier',
        },
        'name': {
            'type': 'string',
            'title': 'Name Title',
        },
        'address': {
            'items': {
                '$ref': '#/definitions/Address',
            },
            'type': 'array',
            'title': 'Address Title',
        },
    },
}

test_list_of_dicts_with_ids_data = [
    # No schema case
    (
        test_list_of_dicts_with_ids_data_sheets,
        None,
        test_list_of_dicts_with_ids_data_result,
        test_list_of_dicts_with_ids_data_cell_source_map,
        test_list_of_dicts_with_ids_data_heading_source_map,
    ),
    # Schema with no titles (same source maps as above)
    (
        test_list_of_dicts_with_ids_data_sheets,
        {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'definitions': {
                'Address': {
                    'type': 'object',
                    'properties': {
                        'house': {
                            'type': 'string',
                        },
                        'id': {
                            'type': 'string',
                        },
                    },
                },
            },
            'properties': {
                'id': {
                    'type': 'string',
                },
                'name': {
                    'type': 'string',
                },
                'address': {
                    'items': {
                        '$ref': '#/definitions/Address',
                    },
                    'type': 'array',
                },
            },
        },
        test_list_of_dicts_with_ids_data_result,
        test_list_of_dicts_with_ids_data_cell_source_map,
        test_list_of_dicts_with_ids_data_heading_source_map,
    ),
    # Schema with titles that aren't used in the headings (same source maps as two cases above)
    (
        test_list_of_dicts_with_ids_data_sheets,
        test_list_of_dicts_with_ids_data_schema_with_titles,
        test_list_of_dicts_with_ids_data_result,
        test_list_of_dicts_with_ids_data_cell_source_map,
        test_list_of_dicts_with_ids_data_heading_source_map,
    ),
    # Schema with titles used in the headings (different source maps)
    (
        [
            {
                'name': 'main',
                'headings': [
                    ' IDENtifiER ',
                    ' NAmE TiTLe ',
                    ' ADDresS TiTLe : 0 : IDENtifiER ',
                    ' ADDresS TiTLe : 0 : HOusE TiTLe '
                ],
                'rows': [
                    ['person1', 'James', 'address1', '15'],
                ],
            },
        ],
        test_list_of_dicts_with_ids_data_schema_with_titles,
        test_list_of_dicts_with_ids_data_result,
        OrderedDict([
            (u'main/0/address/0/house', [('main', 'D', 2, ' ADDresS TiTLe : 0 : HOusE TiTLe ')]),
            (u'main/0/address/0/id', [('main', 'C', 2, ' ADDresS TiTLe : 0 : IDENtifiER ')]),
            (u'main/0/id', [('main', 'A', 2, ' IDENtifiER ')]),
            (u'main/0/name', [('main', 'B', 2, ' NAmE TiTLe ')]),
            (u'main/0/address/0', [('main', 2)]),
            (u'main/0', [('main', 2)])
        ]),
        OrderedDict([
            ('main/address/house', [('main', ' ADDresS TiTLe : 0 : HOusE TiTLe ')]),
            ('main/address/id', [('main', ' ADDresS TiTLe : 0 : IDENtifiER ')]),
            ('main/id', [('main', ' IDENtifiER ')]),
            ('main/name', [('main', ' NAmE TiTLe ')]),
        ]),
    )
]


@pytest.mark.parametrize(
    'sheets, schema, expected_result, expected_cell_source_map, expected_heading_source_map',
    test_list_of_dicts_with_ids_data
)
def test_list_of_dicts_with_ids(sheets, schema, expected_result, expected_cell_source_map, expected_heading_source_map):
    result, cell_source_map, heading_source_map = run(sheets, schema=schema, source_maps=True)
    assert expected_result == result
    if WITH_CELLS:
        assert expected_cell_source_map == cell_source_map
        assert expected_heading_source_map == heading_source_map


test_arrangement_data_sheets = (
    # Normalised
    (
        [
            {
                'name': 'main',
                'headings': ['id', 'name'],
                'rows': [
                    ['PERSON-james', 'James'],
                    ['PERSON-bob',   'Bob'],
                ]
            },
            {
                'name': 'addresses',
                'headings': ['id', 'address/0/house', 'address/0/town'],
                'rows': [
                    ['PERSON-james', '1', 'London'],
                    ['PERSON-james', '2', 'Birmingham'],
                    ['PERSON-bob',   '3', 'Leeds'],
                    ['PERSON-bob',   '4', 'Manchester'],
                ]
            },
        ],
        OrderedDict([
            # Cells
            ('main/0/address/0/house', [('addresses', 'B', 2, 'address/0/house')]),
            ('main/0/address/0/town',  [('addresses', 'C', 2, 'address/0/town')]),
            ('main/0/address/1/house', [('addresses', 'B', 3, 'address/0/house')]),
            ('main/0/address/1/town',  [('addresses', 'C', 3, 'address/0/town')]),
            ('main/0/id',              [('main', 'A', 2, 'id'), ('addresses', 'A', 2, 'id'), ('addresses', 'A', 3, 'id')]),
            ('main/0/name',            [('main', 'B', 2, 'name')]),
            ('main/1/address/0/house', [('addresses', 'B', 4, 'address/0/house')]),
            ('main/1/address/0/town',  [('addresses', 'C', 4, 'address/0/town')]),
            ('main/1/address/1/house', [('addresses', 'B', 5, 'address/0/house')]),
            ('main/1/address/1/town',  [('addresses', 'C', 5, 'address/0/town')]),
            ('main/1/id',              [('main', 'A', 3, 'id'), ('addresses', 'A', 4, 'id'), ('addresses', 'A', 5, 'id')]),
            ('main/1/name',            [('main', 'B', 3, 'name')]),
            # Rows
            ('main/0/address/0', [('addresses', 2)]),
            ('main/0/address/1', [('addresses', 3)]),
            ('main/0',           [('main', 2), ('addresses', 2), ('addresses', 3)]),
            ('main/1/address/0', [('addresses', 4)]),
            ('main/1/address/1', [('addresses', 5)]),
            ('main/1',           [('main', 3), ('addresses', 4), ('addresses', 5)])
        ]),
        OrderedDict([
            ('main/address/house', [('addresses', 'address/0/house')]),
            ('main/address/town',  [('addresses', 'address/0/town')]),
            ('main/id',            [('main', 'id'), ('addresses', 'id')]),
            ('main/name',          [('main', 'name')])
        ]),
        (
            [
                'addresses:A2',
                'addresses:A3',
                'addresses:A4',
                'addresses:A5',
                'addresses:B2',
                'addresses:B3',
                'addresses:B4',
                'addresses:B5',
                'addresses:C2',
                'addresses:C3',
                'addresses:C4',
                'addresses:C5',
                'main:A2',
                'main:A3',
                'main:B2',
                'main:B3',
            ],
            {
                'main:2': 1,
                'main:3': 1,
                'addresses:2': 2,
                'addresses:3': 2,
                'addresses:5': 2,
                'addresses:4': 2,
            }
        ),
        [
            'addresses:address/0/house',
            'addresses:address/0/town',
            'addresses:id',
            'main:id',
            'main:name'
        ]
    ),
    (
        # New columns for each item of the array
        [
            {
                'name': 'main',
                'headings': ['id', 'name', 'address/0/house', 'address/0/town', 'address/1/house', 'address/1/town'],
                'rows': [
                    ['PERSON-james', 'James', '1', 'London', '2', 'Birmingham'],
                    ['PERSON-bob',   'Bob',   '3', 'Leeds',  '4', 'Manchester'],
                ]
            },
        ],
        OrderedDict([
            ('main/0/address/0/house', [('main', 'C', 2, 'address/0/house')]),
            ('main/0/address/0/town', [('main', 'D', 2, 'address/0/town')]),
            ('main/0/address/1/house', [('main', 'E', 2, 'address/1/house')]),
            ('main/0/address/1/town', [('main', 'F', 2, 'address/1/town')]),
            ('main/0/id', [('main', 'A', 2, 'id')]),
            ('main/0/name', [('main', 'B', 2, 'name')]),
            ('main/1/address/0/house', [('main', 'C', 3, 'address/0/house')]),
            ('main/1/address/0/town', [('main', 'D', 3, 'address/0/town')]),
            ('main/1/address/1/house', [('main', 'E', 3, 'address/1/house')]),
            ('main/1/address/1/town', [('main', 'F', 3, 'address/1/town')]),
            ('main/1/id', [('main', 'A', 3, 'id')]),
            ('main/1/name', [('main', 'B', 3, 'name')]),
            ('main/0/address/0', [('main', 2)]),
            ('main/0/address/1', [('main', 2)]),
            ('main/0', [('main', 2)]),
            ('main/1/address/0', [('main', 3)]),
            ('main/1/address/1', [('main', 3)]),
            ('main/1', [('main', 3)])
        ]),
        OrderedDict([
            # Note that you get two headings because there are two de-normalised versions
            ('main/address/house', [('main', 'address/0/house'), ('main', 'address/1/house')]),
            ('main/address/town', [('main', 'address/0/town'), ('main', 'address/1/town')]),
            ('main/id', [('main', 'id')]),
            ('main/name', [('main', 'name')])
        ]),
        (
            [
                'main:A2',
                'main:A3',
                'main:B2',
                'main:B3',
                'main:C2',
                'main:C3',
                'main:D2',
                'main:D3',
                'main:E2',
                'main:E3',
                'main:F2',
                'main:F3',
            ],
            {
                # XXX Note that this is 3 since there are 3 unique dictionaries
                'main:2': 3,
                'main:3': 3,
            }
        ),
        [
            'main:address/0/house',
            'main:address/0/town',
            'main:address/1/house',
            'main:address/1/town',
            'main:id',
            'main:name',
        ]
    ),
    (
        # Repeated rows
        [
            {
                'name': 'main',
                'headings': ['id', 'name', 'address/0/house', 'address/0/town'],
                'rows': [
                    ['PERSON-james', 'James', '1', 'London'],
                    ['PERSON-james', 'James', '2', 'Birmingham'],
                    ['PERSON-bob',   'Bob',   '3', 'Leeds'],
                    ['PERSON-bob',   'Bob',   '4', 'Manchester'],
                ]
            },
        ],
        OrderedDict([
            ('main/0/address/0/house', [('main', 'C', 2, 'address/0/house')]),
            ('main/0/address/0/town', [('main', 'D', 2, 'address/0/town')]),
            ('main/0/address/1/house', [('main', 'C', 3, 'address/0/house')]),
            ('main/0/address/1/town', [('main', 'D', 3, 'address/0/town')]),
            ('main/0/id', [('main', 'A', 2, 'id'), ('main', 'A', 3, 'id')]),
            ('main/0/name', [('main', 'B', 2, 'name'), ('main', 'B', 3, 'name')]),

            ('main/1/address/0/house', [('main', 'C', 4, 'address/0/house')]),
            ('main/1/address/0/town', [('main', 'D', 4, 'address/0/town')]),
            ('main/1/address/1/house', [('main', 'C', 5, 'address/0/house')]),
            ('main/1/address/1/town', [('main', 'D', 5, 'address/0/town')]),
            ('main/1/id', [('main', 'A', 4, 'id'), ('main', 'A', 5, 'id')]),
            ('main/1/name', [('main', 'B', 4, 'name'), ('main', 'B', 5, 'name')]),

            ('main/0/address/0', [('main', 2)]),
            ('main/0/address/1', [('main', 3)]),
            ('main/0', [('main', 2), ('main', 3)]),

            ('main/1/address/0', [('main', 4)]),
            ('main/1/address/1', [('main', 5)]),
            ('main/1', [('main', 4), ('main', 5)])
        ]),
        OrderedDict([
            ('main/address/house', [('main', 'address/0/house')]),
            ('main/address/town', [('main', 'address/0/town')]),
            ('main/id', [('main', 'id')]),
            ('main/name', [('main', 'name')])
        ]),
        (
            [
                'main:A2',
                'main:A3',
                'main:A4',
                'main:A5',
                'main:B2',
                'main:B3',
                'main:B4',
                'main:B5',
                'main:C2',
                'main:C3',
                'main:C4',
                'main:C5',
                'main:D2',
                'main:D3',
                'main:D4',
                'main:D5',
            ],
            {
                'main:2': 2,
                'main:3': 2,
                'main:5': 2,
                'main:4': 2
            }
        ),
        [
            'main:address/0/house',
            'main:address/0/town',
            'main:id',
            'main:name',
        ],
    )
)


@pytest.mark.parametrize(
    (
        'sheets,'
        'expected_cell_source_map,'
        'expected_heading_source_map,'
        'expected_original_cell_and_row_locations,'
        'expected_original_heading_locations'
    ),
    test_arrangement_data_sheets
)
def test_arrangement(
    sheets,
    expected_cell_source_map,
    expected_heading_source_map,
    expected_original_cell_and_row_locations,
    expected_original_heading_locations
):
    expected_result = [
        OrderedDict([
            ('id', 'PERSON-james'),
            ('name', 'James'),
            ('address', [
                OrderedDict([
                    ('house', '1'),
                    ('town', 'London'),
                ]),
                OrderedDict([
                    ('house', '2'),
                    ('town', 'Birmingham'),
                ])
            ]),
        ]),
        OrderedDict([
            ('id', 'PERSON-bob'),
            ('name', 'Bob'),
            ('address', [
                OrderedDict([
                    ('house', '3'),
                    ('town', 'Leeds'),
                ]),
                OrderedDict([
                    ('house', '4'),
                    ('town', 'Manchester'),
                ])
            ]),
        ]),
    ]
    actual_result, actual_cell_source_map, actual_heading_source_map = run(sheets, source_maps=True)
    actual_original_cell_and_row_locations = original_cell_and_row_locations(actual_cell_source_map or {})
    actual_original_heading_locations = original_headings(actual_heading_source_map or {})
    assert expected_result == actual_result
    if WITH_CELLS:
        assert expected_cell_source_map == actual_cell_source_map
        assert expected_heading_source_map == actual_heading_source_map
        assert expected_original_cell_and_row_locations == actual_original_cell_and_row_locations
        assert expected_original_heading_locations == actual_original_heading_locations


class HeadingListInput(SpreadsheetInput):
    def __init__(self, sheets, headings, **kwargs):
        self.sheets = sheets
        self.headings = headings
        super(HeadingListInput, self).__init__(**kwargs)

    def get_sheet_lines(self, sheet_name):
        return self.sheets[sheet_name]

    def get_sheet_headings(self, sheet_name):
        return self.headings[sheet_name]

    def read_sheets(self):
        self.sub_sheet_names = list(self.sheets.keys())
        self.sub_sheet_names.remove(self.main_sheet_name)


def run(sheets, schema=None, source_maps=False):
    if not WITH_CELLS:
        source_maps = False
    input_headings = OrderedDict()
    input_sheets = OrderedDict()
    for sheet in sheets:
        rows = []
        for row in sheet['rows']:
            rows.append(OrderedDict(zip(sheet['headings'], row)))
        input_sheets[sheet['name']] = rows
        input_headings[sheet['name']] = sheet['headings']
    if schema is not None:
        spreadsheet_input = HeadingListInput(
            input_sheets,
            input_headings,
            main_sheet_name=sheets[0]['name'],  # Always use the first sheet as the main one
            root_id='',                         # QUESTION: I don't understand root_id
            convert_titles=True,                # Without this, the titles aren't understood
        )
        # Without this, the $ref entries in the schema aren't resolved.
        dereferenced_schema = JsonRef.replace_refs(schema)
        # raise Exception(dereferenced_schema)
        parser = SchemaParser(
            root_schema_dict=dereferenced_schema,
            main_sheet_name=sheets[0]['name'],
            root_id='main',
            rollup=True
        )
        parser.parse()
        spreadsheet_input.parser = parser
    else:
        spreadsheet_input = HeadingListInput(
            input_sheets,
            input_headings,
            main_sheet_name=sheets[0]['name'],
            root_id='',
        )
    spreadsheet_input.read_sheets()
    if source_maps:
        result, cell_source_map_data, heading_source_map_data = spreadsheet_input.fancy_unflatten()
        return result, cell_source_map_data, heading_source_map_data
    else:
        return spreadsheet_input.unflatten(), None, None
