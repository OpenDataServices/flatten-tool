# -*- coding: utf-8 -*-
"""
Tests of unflatten method of the SpreadsheetInput class from input.py
This file only covers tests for the main sheet. Tests for multiple sheets are in test_input_SpreadsheetInput_unflatten_multiplesheets.py

"""
from __future__ import unicode_literals
from .test_input_SpreadsheetInput import ListInput
from flattentool.schema import SchemaParser
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime
import copy
from six import text_type

def inject_root_id(root_id, d):
    """
    Insert the appropriate root id, with the given value, into the dictionary d and return.
    """
    d = copy.copy(d)
    if root_id != '':
        d.update({root_id: d['ROOT_ID']})
    del d['ROOT_ID']
    return d

UNICODE_TEST_STRING = 'éαГ😼𝒞人'

# TODO Actually create appropriate schema
SCHEMA = {}

# ROOT_ID will be replace by the appropirate root_id name in the test (e.g. ocid)
testdata = [
    # Flat
    (
        [{
            'ROOT_ID': 1,
            'Identifier': 2,
            'testA': 3
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testA': 3
        }],
        [{'ROOT_ID': 1, 'id': 2, 'testA': 3}]
    ),
    # Nested
    (
        [{
            'ROOT_ID': 1,
            'Identifier': 2,
            'testA/testB': 3,
            'testA/testC': 4,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testA/testB': 3,
            'testA/testC': 4,
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testA': {'testB': 3, 'testC': 4}
        }]
    ),
    # Unicode
    (
        [{
            'ROOT_ID': UNICODE_TEST_STRING,
            'A title': UNICODE_TEST_STRING
        }],
        [{
            'ROOT_ID': UNICODE_TEST_STRING,
            'testA': UNICODE_TEST_STRING
        }],
        [{
            'ROOT_ID': UNICODE_TEST_STRING,
            'testA': UNICODE_TEST_STRING
        }]
    ),
    # Rollup
    (
        [{
            'ROOT_ID': 1,
            'Identifier': 2,
            'testA[]/id': 3,
            'testA[]/testB': 4
        }],
        [{
            'ROOT_ID': 1,
            'id': 2,
            'testA[]/id': 3,
            'testA[]/testB': 4
        }],
        [{
            'ROOT_ID': 1, 'id': 2, 'testA': [{
                'id': 3, 'testB': 4
            }]
        }]
    ),
    # Rollup without an ID
    (
        [{
            'ROOT_ID': '1',
            'Identifier': '2',
            'testA[]/testB': '3',
        }],
        [{
            'ROOT_ID': '1',
            'testA[]/id': '2',
            'testA[]/testB': '3',
        }],
        [{
            'ROOT_ID': '1',
            'testA': [{
                'id': '2',
                'testB': '3'
            }]
        }]
    ),
    # Empty
    (
        [{
            'ROOT_ID': '',
            'Identifier': '',
            'testA:number': '',
            'testB:boolean': '',
            'testC:array': '',
            'testD:string': '',
            'testE': '',
        }],
        [{
            'ROOT_ID': '',
            'id:integer': '',
            'testA:number': '',
            'testB:boolean': '',
            'testC:array': '',
            'testD:string': '',
            'testE': '',
        }],
        []
    ),
    # Empty except for root id
    (
        [{
            'ROOT_ID': 1,
            'Identifier': '',
            'testA:number': '',
            'testB:boolean': '',
            'testC:array': '',
            'testD:string': '',
            'testE': '',
        }],
        [{
            'ROOT_ID': 1,
            'id:integer': '',
            'testA:number': '',
            'testB:boolean': '',
            'testC:array': '',
            'testD:string': '',
            'testE': '',
        }],
        [{
            'ROOT_ID': 1
        }]
    )
]

# Convert titles modes: with appropirate schema, without, off
@pytest.mark.parametrize('convert_titles,use_schema,use_input_titles', [
    (False, False, False),  # Test without titles support at all
    (True, False, False),   # Test that non-titles convert properly with convert_titles on
    (True, True, False),    # Test that non-titles convert properly with
                            # convert_titles on, and an appropriate schema
    pytest.mark.xfail((True, True, True)),     # Test that actual titles convert
    ])
@pytest.mark.parametrize('root_id,root_id_kwargs',
    [
        ('ocid', {}), # If not root_id kwarg is passed, then a root_id of ocid is assumed
        ('ocid', {'root_id': 'ocid'}),
        ('custom', {'root_id': 'custom'}),
        ('', {'root_id': ''})
    ])
@pytest.mark.parametrize('input_list_titles,input_list,,expected_output_list', testdata)
def test_unflatten(convert_titles, use_schema, use_input_titles, root_id, root_id_kwargs, input_list, input_list_titles, expected_output_list, recwarn):
    if use_input_titles:
        input_list = input_list_titles
    extra_kwargs = {'convert_titles': convert_titles}
    extra_kwargs.update(root_id_kwargs)
    spreadsheet_input = ListInput(
        sheets={
            'custom_main': [
                inject_root_id(root_id, input_row) for input_row in input_list
            ]
        },
        main_sheet_name='custom_main',
        **extra_kwargs)
    spreadsheet_input.read_sheets()
    if convert_titles:
        parser = SchemaParser(
            root_schema_dict=SCHEMA if use_schema else {},
            use_titles=True
        )
        parser.parse()
        spreadsheet_input.parser = parser
    expected_output_list = [
        inject_root_id(root_id, expected_output_dict) for expected_output_dict in expected_output_list
    ]
    if expected_output_list == [{}]:
        # We don't expect an empty dictionary
        expected_output_list = []
    assert list(spreadsheet_input.unflatten()) == expected_output_list
    # We expect no warnings
    if not convert_titles: # TODO what are the warnings here
        assert recwarn.list == []

