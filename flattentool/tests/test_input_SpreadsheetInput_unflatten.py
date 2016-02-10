# -*- coding: utf-8 -*-
"""
Tests of unflatten method of the SpreadsheetInput class from input.py
"""
from __future__ import unicode_literals
from .test_input_SpreadsheetInput import ListInput
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime
from six import text_type

class TestUnflatten(object):
    def test_main_sheet_flat(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA': 3,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'testA': 3}
        ]

    def test_main_sheet_nonflat(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA/testB': 3,
                        'testA/testC': 4,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'testA': {'testB': 3, 'testC': 4}}
        ]

    def test_basic_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'custom_main/id:subField': 2,
                        'testA': 3,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'subField': [{'testA': 3}]}
        ]

    def test_nested_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'custom_main/id:testA/subField': 2,
                        'testB': 3,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'testA': {'subField': [{'testB': 3}]}}
        ]

    def test_basic_two_sub_sheets(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    OrderedDict([
                        ('ocid', 1),
                        ('id', 2),
                    ])
                ],
                'sub1': [
                    {
                        'ocid': 1,
                        'custom_main/id:sub1Field': 2,
                        'id': 3,
                        'testA': 4,
                    }
                ],
                'sub2': [
                    {
                        'ocid': 1,
                        'custom_main/id:sub1Field': 2,
                        'custom_main/sub1Field[]/id:sub2Field': 3,
                        'testB': 5,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert list(unflattened[0]) == ['ocid', 'id', 'sub1Field']
        assert unflattened[0]['ocid'] == 1
        assert unflattened[0]['id'] == 2
        assert unflattened[0]['sub1Field'] == [
            {
                'id': 3,
                'testA': 4,
                'sub2Field': [
                    {
                        'testB': 5
                    }
                ]
            }
        ]

    def test_unicode(self):
        unicode_string = 'éαГ😼𝒞人'
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'testA': unicode_string,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'testA': unicode_string}
        ]

    def test_conflicting_ids(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'custom_main/id': 2,
                        'custom_main/testA[]/id:subField': 1,
                        'custom_main/testB[]/id:subField': 1,
                        'testC': 3,
                    },
                    {
                        'ocid': 1,
                        'custom_main/id': 2,
                        'custom_main/testA[]/id:subField': 1,
                        'custom_main/testB[]/id:subField': '',
                        'testC': 4,
                    }
                ],
                'testA': [
                    {
                        'ocid': 1,
                        'custom_main/id': 2,
                        'id': 1,
                    }
                ],
                'testB': [
                    {
                        'ocid': 1,
                        'custom_main/id': 2,
                        'id': 1,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        # We should have a warning about conflicting ID fields
        w = recwarn.pop(UserWarning)
        assert 'Multiple conflicting ID fields' in text_type(w.message)
        # (line number includes an assumed header line)
        assert 'line 2 of sheet sub' in text_type(w.message)
        # Only one top level object should have been outputted
        assert len(unflattened) == 1
        # Check that the valid data is outputted correctly
        assert spreadsheet_input.unflatten()[0] == \
            {
                'ocid': 1,
                'id': 2,
                'testA': [{
                    'id': 1,
                    'subField': [{'testC': 4}]
                }],
                'testB': [{
                    'id': 1
                }]
            }

    def test_nested_id(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'custom_main/id:subField': 2,
                        'id': 3,
                        'testA/id': 4,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'ocid': 1, 'id': 2, 'subField': [{'id': 3, 'testA': {'id': 4}}]}
        ]

    def test_missing_columns(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'ocid': 1,
                        'custom_main/id:subField': '',
                        'id': 3,
                        'testA/id': 4,
                    },
                    {
                        'ocid': 1,
                        'custom_main/id:subField': 2,
                        'id': 3,
                        'testA': 5,
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        # We should have a warning about conflicting ID fields
        w = recwarn.pop(UserWarning)
        assert 'no parent id fields populated' in text_type(w.message)
        assert 'Line 2 of sheet sub' in text_type(w.message)
        # Check that following lines are parsed correctly
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'subField': [{'id': 3, 'testA': 5}]}
        ]


class TestUnflattenRollup(object):
    def test_same_rollup(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA[]/id': 3,
                        'testA[]/testB': 4
                    }
                ],
                'testA': [
                    {
                        'ocid': 1,
                        'main/id': 2,
                        'id': 3,
                        'testB': 4,
                    }
                ]
            },
            main_sheet_name='main'
        )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'testA': [{'id': 3, 'testB': 4}]}
        ]
        # We expect no warnings
        assert recwarn.list == []

    def test_conflicting_rollup(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA[]/id': 3,
                        'testA[]/testB': 4
                    }
                ],
                'testA': [
                    {
                        'ocid': 1,
                        'main/id': 2,
                        'id': 3,
                        'testB': 5,
                    }
                ]
            },
            main_sheet_name='main'
        )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'testA': [{'id': 3, 'testB': 5}]}
        ]
        # We should have a warning about the conflist
        w = recwarn.pop(UserWarning)
        assert 'Conflict between main sheet and sub sheet' in text_type(w.message)


class TestUnflattenEmpty(object):
    def test_all_empty(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': '',
                        'id:integer': '',
                        'testA:number': '',
                        'testB:boolean': '',
                        'testC:array': '',
                        'testD:string': '',
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 0

    def test_sub_sheet_empty(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [],
                'subsheet': [
                    {
                        'ocid': '',
                        'id:integer': '',
                        'testA:number': '',
                        'testB:boolean': '',
                        'testC:array': '',
                        'testD:string': '',
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 0

    def test_types_empty(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'ocid': '1',
                        'id:integer': '',
                        'testA:number': '',
                        'testB:boolean': '',
                        'testC:array': '',
                        'testD:string': '',
                        'testE': '',
                    }
                ]
            },
            main_sheet_name='custom_main')
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 1
        assert output[0] == {'ocid': '1'}


def test_1n_override():
    spreadsheet_input = ListInput(
        sheets={
            'custom_main': [
                {
                    'ocid': '1',
                    'id': '4',
                    'testA[]/id': '2',
                    'testA[]/testB': '3',
                }
            ]
        },
        main_sheet_name='custom_main')
    spreadsheet_input.read_sheets()
    output = list(spreadsheet_input.unflatten())
    assert len(output) == 1
    assert output[0] == {
        'ocid': '1',
        'id': '4',
        'testA': [{'id': '2', 'testB': '3'}]
    }


def test_1n_override_no_id():
    spreadsheet_input = ListInput(
        sheets={
            'custom_main': [
                {
                    'ocid': '1',
                    'testA[]/id': '2',
                    'testA[]/testB': '3',
                }
            ]
        },
        main_sheet_name='custom_main')
    spreadsheet_input.read_sheets()
    output = list(spreadsheet_input.unflatten())
    assert len(output) == 1
    assert output[0] == {
        'ocid': '1',
        'testA': [{'id': '2', 'testB': '3'}]
    }


class TestUnflattenCustomRootID(object):
    def test_main_sheet_flat(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'custom': 1,
                        'id': 2,
                        'testA': 3,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='custom')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'custom': 1, 'id': 2, 'testA': 3}
        ]

    def test_main_sheet_nonflat(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'custom': 1,
                        'id': 2,
                        'testA/testB': 3,
                        'testA/testC': 4,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='custom')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'custom': 1, 'id': 2, 'testA': {'testB': 3, 'testC': 4}}
        ]

    def test_basic_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'custom': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'custom': 1,
                        'custom_main/id:subField': 2,
                        'testA': 3,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='custom')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'custom': 1, 'id': 2, 'subField': [{'testA': 3}]}
        ]

    def test_nested_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'custom': 1,
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'custom': 1,
                        'custom_main/id:testA/subField': 2,
                        'testB': 3,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='custom')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'custom': 1, 'id': 2, 'testA': {'subField': [{'testB': 3}]}}
        ]

    def test_basic_two_sub_sheets(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    OrderedDict([
                        ('custom', 1),
                        ('id', 2),
                    ])
                ],
                'sub1': [
                    {
                        'custom': 1,
                        'custom_main/id:sub1Field': 2,
                        'id': 3,
                        'testA': 4,
                    }
                ],
                'sub2': [
                    {
                        'custom': 1,
                        'custom_main/id:sub1Field': 2,
                        'custom_main/sub1Field[]/id:sub2Field': 3,
                        'testB': 5,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='custom')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert list(unflattened[0]) == ['custom', 'id', 'sub1Field']
        assert unflattened[0]['custom'] == 1
        assert unflattened[0]['id'] == 2
        assert unflattened[0]['sub1Field'] == [
            {
                'id': 3,
                'testA': 4,
                'sub2Field': [
                    {
                        'testB': 5
                    }
                ]
            }
        ]


class TestUnflattenNoRootID(object):
    def test_main_sheet_flat(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'id': 2,
                        'testA': 3,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'id': 2, 'testA': 3}
        ]

    def test_main_sheet_nonflat(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'id': 2,
                        'testA/testB': 3,
                        'testA/testC': 4,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'id': 2, 'testA': {'testB': 3, 'testC': 4}}
        ]

    def test_basic_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'custom_main/id:subField': 2,
                        'testA': 3,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'id': 2, 'subField': [{'testA': 3}]}
        ]

    def test_nested_sub_sheet(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    {
                        'id': 2,
                    }
                ],
                'sub': [
                    {
                        'custom_main/id:testA/subField': 2,
                        'testB': 3,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='')
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            {'id': 2, 'testA': {'subField': [{'testB': 3}]}}
        ]

    def test_basic_two_sub_sheets(self):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    OrderedDict([
                        ('id', 2),
                    ])
                ],
                'sub1': [
                    {
                        'custom_main/id:sub1Field': 2,
                        'id': 3,
                        'testA': 4,
                    }
                ],
                'sub2': [
                    {
                        'custom_main/id:sub1Field': 2,
                        'custom_main/sub1Field[]/id:sub2Field': 3,
                        'testB': 5,
                    }
                ]
            },
            main_sheet_name='custom_main',
            root_id='')
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert unflattened[0]['id'] == 2
        assert unflattened[0]['sub1Field'] == [
            {
                'id': 3,
                'testA': 4,
                'sub2Field': [
                    {
                        'testB': 5
                    }
                ]
            }
        ]
