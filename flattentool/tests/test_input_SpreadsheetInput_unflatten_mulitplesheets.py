# -*- coding: utf-8 -*-
"""
Tests of unflatten method of the SpreadsheetInput class from input.py

Tests that only apply for multiple sheets.
"""
from __future__ import unicode_literals
from .test_input_SpreadsheetInput import ListInput
from .test_input_SpreadsheetInput_unflatten import ROOT_ID_PARAMS, create_schema, inject_root_id
from flattentool.schema import SchemaParser
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime


testdata_multiplesheets = [
    (
        'Basic sub sheet',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                },
                {
                    'ROOT_ID': 1,
                    'id': 3,
                }
            ],
            'testArr': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testArr/0/testC': '3',
                },
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testArr/0/testC': '4',
                }
            ]
        },
        [
            {
                'ROOT_ID': 1,
                'id': 2,
                'testArr': [
                    {'testC': '3'},
                    {'testC': '4'},
                ]
            },
            {
                'ROOT_ID': 1,
                'id': 3
            }
        ],
        [],
        True
    ),
    (
        'Nested sub sheet (with id)',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testB/id': 3,
                    'testB/testC': 4,
                }
            ],
            'tes_subField': [
                # It used to be neccesary to supply testA/id in this
                # situation, but now it's optional
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testB/id': 3,
                    'testB/subField/0/testD': 5,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testB': {
                'id': 3,
                'testC': 4,
                'subField': [{'testD': 5}]
            }}
        ],
        [],
        True
    ),
    (
        'Nested sub sheet (without id)',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testB/id': 3,
                    'testB/testC': 4,
                }
            ],
            'sub': [
                # It used to be neccesary to supply testA/id in this
                # situation, but now it's optional
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testB/subField/0/testD': 5,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testB': {
                'id': 3,
                'testC': 4,
                'subField': [{'testD': 5}]
            }}
        ],
        [],
        False
    ),
    (
        'Basic two sub sheets',
        OrderedDict([
            ('custom_main', [
                OrderedDict([
                    ('ROOT_ID', 1),
                    ('id', 2),
                ]),
                OrderedDict([
                    ('ROOT_ID', 1),
                    ('id', 6),
                ])
            ]),
            ('sub1Field', [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'sub1Field/0/id': 3,
                    'sub1Field/0/testA': 4,
                }
            ]),
            ('sub_sub2Field', [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'sub1Field/0/id': 3,
                    'sub1Field/0/sub2Field/0/testB': 5,
                }
            ])
        ]),
        [
            OrderedDict([
                ('ROOT_ID', 1),
                ('id', 2),
                ('sub1Field', [
                    {
                        'id': 3,
                        'testA': 4,
                        'sub2Field': [
                            {
                                'testB': 5
                            }
                        ]
                    }
                ])
            ]),
            {
                'ROOT_ID':1,
                'id': 6
            }
        ],
        [],
        True
    ),
    (
        'Nested id',
         {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                }
            ],
            'subField': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'subField/0/id': 3,
                    'subField/0/testA/id': 4,
                }
            ]
        },
        [{'ROOT_ID': 1, 'id': 2, 'subField': [{'id': 3, 'testA': {'id': 4}}]}],
        [],
        True
    ),
    (
        'Missing columns',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                }
            ],
            'sub': [
                {
                    'ROOT_ID': 1,
                    'id': '',
                    'subField/0/id': 3,
                    'subField/0/testA': 4,
                },
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'subField/0/id': 3,
                    'subField/0/testA': 5,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'subField': [{'id': 3, 'testA': 5}]},
            {'ROOT_ID': 1, 'subField': [{'id': 3, 'testA': 4}]},
        ],
        [],
        False
    ),
    (
        'Unmatched id',
        OrderedDict([
            ('custom_main', [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                }
            ]),
            ('sub', [
                {
                    'ROOT_ID': 1,
                    'id': 100,
                    'subField/0/id': 3,
                    'subField/0/testA': 4,
                },
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'subField/0/id': 3,
                    'subField/0/testA': 5,
                }
            ])
        ]),
        [
            {'ROOT_ID': 1, 'id': 2, 'subField': [{'id': 3, 'testA': 5}]},
            {'ROOT_ID': 1, 'id': 100, 'subField': [{'id': 3, 'testA': 4}]},
        ],
        [],
        False
    ),
    (
        'Test same rollup',
        {
            'main': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testC': 3,
                    'testArr/0/id': '4',
                    'testArr/0/testB': '5',
                },
                {
                    'ROOT_ID': 6,
                    'id': 7,
                    'testC': 8,
                    'testArr/0/testB': '9',
                }
            ],
            'testArr': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testArr/0/id': '4',
                    'testArr/0/testB': '5',
                },
                {
                    'ROOT_ID': 6,
                    'id': 7,
                    'testArr/0/testB': '9',
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testC':3, 'testArr': [{'id': '4', 'testB': '5'}]},
            {'ROOT_ID': 6, 'id': 7, 'testC':8, 'testArr': [
                {'testB': '9'}, {'testB': '9'}
                # We have duplicates here because there's no ID to merge these
                # on. This is different to the old behaviour. Issue filed at
                # https://github.com/OpenDataServices/flatten-tool/issues/99
            ]},
        ],
        [],
        False
    ),
    (
        'Test conflicting rollup',
        OrderedDict([
            ('main', [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testArr/0/id': '3',
                    'testArr/0/testB': '4'
                }
            ]),
            ('testArr', [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testArr/0/id': '3',
                    'testArr/0/testB': '5',
                }
            ])
        ]),
        [
            {
                'ROOT_ID': 1,
                'id': 2,
                'testArr': [{
                    'id': '3',
                    'testB': '4'
                    # (Since sheets are parsed in the order they appear, and the first value is used).
                }]
            }
        ],
        ['Conflict when merging field "testB" for ROOT_ID "1", id "2" in sheet testA: "4" != "5"'],
        False
    ),
    (
        'Unflatten empty',
        {
            'custom_main': [],
            'subsheet': [
                {
                    'ROOT_ID': '',
                    'id': '',
                    'testA': '',
                    'testB': '',
                    'testC': '',
                    'testD': '',
                }
            ]
        },
        [],
        [],
        False
    )
]



testdata_multiplesheets_pointer = [
    (
        'with schema',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'id': '2',
                    'testA': 3
                }
            ],
            'sub': [
                {
                    'ROOT_ID': 1,
                    'id': 2,
                    'testArr/testB': 4 # test that we can infer this an array from schema
                }
            ]
        },
        [{
            'ROOT_ID': 1,
            'id': 2, # check that we join correctly when this gets converted to an
                     # integer because of the schema type
            'testA': 3,
            'testArr': [{
                'testB': '4'
            }]
        }],
        []
    )
]


testdata_multiplesheets_titles = [
    (
        'Basic sub sheet',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                },
                {
                    'ROOT_ID': 1,
                    'Identifier': 3,
                }
            ],
            'testArr': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:C title': '3',
                },
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:C title': '4',
                }
            ]
        },
        [
            {
                'ROOT_ID': 1,
                'id': 2,
                'testArr': [
                    {'testC': '3'},
                    {'testC': '4'},
                ]
            },
            {
                'ROOT_ID': 1,
                'id': 3
            }
        ],
        [],
        True
    ),
    (
        'Nested sub sheet (with id)',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'B title:Identifier': 3,
                    'B title:C title': 4,
                }
            ],
            'tes_subField': [
                # It used to be neccesary to supply testA/id in this
                # situation, but now it's optional
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'B title:Identifier': 3,
                    'B title:Sub title:E title': 5,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testB': {
                'id': 3,
                'testC': 4,
                'subField': [{'testE': 5}]
            }}
        ],
        [],
        True
    ),
    (
        'Nested sub sheet (without id)',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'B title:Identifier': 3,
                    'B title:C title': 4,
                }
            ],
            'sub': [
                # It used to be neccesary to supply testA/id in this
                # situation, but now it's optional
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'B title:Sub title:E title': 5,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testB': {
                'id': 3,
                'testC': 4,
                'subField': [{'testE': 5}]
            }}
        ],
        [],
        False
    ),
    (
        'Basic two sub sheets',
        OrderedDict([
            ('custom_main', [
                OrderedDict([
                    ('ROOT_ID', 1),
                    ('Identifier', 2),
                ]),
                OrderedDict([
                    ('ROOT_ID', 1),
                    ('Identifier', 6),
                ])
            ]),
            ('testArr', [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': '3',
                    'Arr title:B title': '4',
                }
            ]),
            ('tes_testNest', [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': '3',
                    'Arr title:Nest title:D title': '5',
                }
            ])
        ]),
        [
            OrderedDict([
                ('ROOT_ID', 1),
                ('id', 2),
                ('testArr', [
                    {
                        'id': '3',
                        'testB': '4',
                        'testNest': [
                            {
                                'testD': '5'
                            }
                        ]
                    }
                ])
            ]),
            {
                'ROOT_ID':1,
                'id': 6
            }
        ],
        [],
        True
    ),
   (
       'Nested id',
        {
           'custom_main': [
               {
                   'ROOT_ID': 1,
                   'Identifier': 2,
               }
           ],
           'testArr': [
               {
                   'ROOT_ID': 1,
                   'Identifier': 2,
                   'Arr title:Identifier': '3',
                   'Arr title:NestObj title:Identifier': '4',
               }
           ]
       },
       [{'ROOT_ID': 1, 'id': 2, 'testArr': [{'id': '3', 'testNestObj': {'id': '4'}}]}],
       [],
       True
   ),
    (
        'Missing columns',
        {
            'custom_main': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                }
            ],
            'sub': [
                {
                    'ROOT_ID': 1,
                    'Identifier': '',
                    'Arr title:Identifier': 3,
                    'Arr title:B title': 4,
                },
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': 3,
                    'Arr title:B title': 5,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testArr': [{'id': '3', 'testB': '5'}]},
            {'ROOT_ID': 1, 'testArr': [{'id': '3', 'testB': '4'}]},
        ],
        [],
        False
    ),
    (
        'Unmatched id',
        OrderedDict([
            ('custom_main', [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                }
            ]),
            ('sub', [
                {
                    'ROOT_ID': 1,
                    'Identifier': 100,
                    'Arr title:Identifier': 3,
                    'Arr title:B title': 4,
                },
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': 3,
                    'Arr title:B title': 5,
                }
            ])
        ]),
        [
            {'ROOT_ID': 1, 'id': 2, 'testArr': [{'id': '3', 'testB': '5'}]},
            {'ROOT_ID': 1, 'id': 100, 'testArr': [{'id': '3', 'testB': '4'}]},
        ],
        [],
        False
    ),
    (
        'Test same rollup',
        {
            'main': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'A title': 3,
                    'Arr title:Identifier': 4,
                    'Arr title:B title': 5,
                },
                {
                    'ROOT_ID': 6,
                    'Identifier': 7,
                    'A title': 8,
                    'Arr title:B title': 9,
                }
            ],
            'testArr': [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': 4,
                    'Arr title:B title': 5,
                },
                {
                    'ROOT_ID': 6,
                    'Identifier': 7,
                    'Arr title:B title': 9,
                }
            ]
        },
        [
            {'ROOT_ID': 1, 'id': 2, 'testA':3, 'testArr': [{'id': '4', 'testB': '5'}]},
            {'ROOT_ID': 6, 'id': 7, 'testA':8, 'testArr': [
                {'testB': '9'}, {'testB': '9'}
                # We have duplicates here because there's no ID to merge these
                # on. This is different to the old behaviour. Issue filed at
                # https://github.com/OpenDataServices/flatten-tool/issues/99
            ]},
        ],
        [],
        False
    ),
    (
        'Test conflicting rollup',
        OrderedDict([
            ('main', [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': '3',
                    'Arr title:B title': '4'
                }
            ]),
            ('testArr', [
                {
                    'ROOT_ID': 1,
                    'Identifier': 2,
                    'Arr title:Identifier': '3',
                    'Arr title:B title': '5',
                }
            ])
        ]),
        [
            {
                'ROOT_ID': 1,
                'id': 2,
                'testArr': [{
                    'id': '3',
                    'testB': '4'
                    # (Since sheets are parsed in the order they appear, and the first value is used).
                }]
            }
        ],
        ['Conflict when merging field "testB" for ROOT_ID "1", id "2" in sheet testA: "4" != "5"'],
        False
    ),
    (
        'Unflatten empty',
        {
            'custom_main': [],
            'subsheet': [
                {
                    'ROOT_ID': '',
                    'Identifier': '',
                    'A title': '',
                    'U title': '',
                }
            ]
        },
        [],
        [],
        False
    )
]


@pytest.mark.parametrize('convert_titles', [True, False])
@pytest.mark.parametrize('use_schema', [True, False])
@pytest.mark.parametrize('root_id,root_id_kwargs', ROOT_ID_PARAMS)
@pytest.mark.parametrize('comment,input_dict,expected_output_list,warning_messages,reversible', testdata_multiplesheets)
def test_unflatten(convert_titles, use_schema, root_id, root_id_kwargs, input_dict, expected_output_list, recwarn, comment, warning_messages, reversible):
    extra_kwargs = {'convert_titles': convert_titles}
    extra_kwargs.update(root_id_kwargs)
    spreadsheet_input = ListInput(
        sheets=OrderedDict([(sheet_name, [inject_root_id(root_id, line) for line in lines]) for sheet_name, lines in input_dict.items()]),
        **extra_kwargs
        )
    spreadsheet_input.read_sheets()

    parser = SchemaParser(
        root_schema_dict=create_schema(root_id) if use_schema else {"properties": {}},
        root_id=root_id,
        rollup=True
    )
    parser.parse()
    spreadsheet_input.parser = parser

    expected_output_list = [
        inject_root_id(root_id, expected_output_dict) for expected_output_dict in expected_output_list
    ]
    assert list(spreadsheet_input.unflatten()) == expected_output_list


@pytest.mark.parametrize('convert_titles', [True, False])
@pytest.mark.parametrize('root_id,root_id_kwargs', ROOT_ID_PARAMS)
@pytest.mark.parametrize('comment,input_dict,expected_output_list,warning_messages', testdata_multiplesheets_pointer)
def test_unflatten_pointer(convert_titles, root_id, root_id_kwargs, input_dict, expected_output_list, recwarn, comment, warning_messages):
    return test_unflatten(convert_titles=convert_titles, use_schema=True, root_id=root_id, root_id_kwargs=root_id_kwargs, input_dict=input_dict, expected_output_list=expected_output_list, recwarn=recwarn, comment=comment, warning_messages=warning_messages, reversible=False)


@pytest.mark.parametrize('comment,input_dict,expected_output_list,warning_messages,reversible', testdata_multiplesheets_titles)
@pytest.mark.parametrize('root_id,root_id_kwargs', ROOT_ID_PARAMS)
def test_unflatten_titles(root_id, root_id_kwargs, input_dict, expected_output_list, recwarn, comment, warning_messages, reversible):
    """
    Essentially the same as test unflatten, except that convert_titles and
    use_schema are always true, as both of these are needed to convert titles
    properly. (and runs with different test data).
    """
    if root_id != '':
        # Skip all tests with a root ID for now, as this is broken
        # https://github.com/OpenDataServices/flatten-tool/issues/84
        pytest.skip()
    return test_unflatten(convert_titles=True, use_schema=True, root_id=root_id, root_id_kwargs=root_id_kwargs, input_dict=input_dict, expected_output_list=expected_output_list, recwarn=recwarn, comment=comment, warning_messages=warning_messages, reversible=reversible)

