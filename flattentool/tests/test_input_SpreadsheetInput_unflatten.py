# -*- coding: utf-8 -*-
"""
Tests of unflatten method of the SpreadsheetInput class from input.py
This file only covers tests for the main sheet. Tests for multiple sheets are in test_input_SpreadsheetInput_unflatten_multiplesheets.py

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

def inject_root_id(root_id, d, value=1):
    """
    Insert the appropriate root id, with the given value, into the dictionary d and return.
    """
    d.update({root_id: value})
    return d

def root_id_kwargs(root_id):
    """
    Return the appropriate keyword arguments to pass to a SpreadsheetInput
    child (generally ListInput in the tests), in order to handle the correct
    root_id (or lack thereof).
    """
    if root_id == 'ocid':
        return {}
    else:
        return {'root_id': root_id}

@pytest.mark.parametrize('root_id', ['ocid', 'custom', ''])
class TestUnflatten(object):
    def test_main_sheet_flat(self, root_id):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    inject_root_id(root_id, {
                        'id': 2,
                        'testA': 3,
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_kwargs(root_id))
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            inject_root_id(root_id, {'id': 2, 'testA': 3})
        ]

    def test_main_sheet_nonflat(self, root_id):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    inject_root_id(root_id, {
                        'id': 2,
                        'testA/testB': 3,
                        'testA/testC': 4,
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_kwargs(root_id))
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            inject_root_id(root_id, {'id': 2, 'testA': {'testB': 3, 'testC': 4}})
        ]

    def test_unicode(self, root_id):
        unicode_string = 'éαГ😼𝒞人'
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    inject_root_id(root_id, {
                        'testA': unicode_string,
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_kwargs(root_id))
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            inject_root_id(root_id, {'testA': unicode_string})
        ]

    def test_rollup(self, recwarn, root_id):
        spreadsheet_input = ListInput(
            sheets={
                'main': [
                    inject_root_id(root_id, {
                        'id': 2,
                        'testA[]/id': 3,
                        'testA[]/testB': 4
                    })
                ]
            },
            main_sheet_name='main',
            **root_id_kwargs(root_id)
        )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert unflattened == [
            inject_root_id(root_id, {'id': 2, 'testA': [{'id': 3, 'testB': 4}]})
        ]
        # We expect no warnings
        assert recwarn.list == []

    def test_rollup_no_id(self, recwarn, root_id):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    inject_root_id(root_id, {
                        'testA[]/id': '2',
                        'testA[]/testB': '3',
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_kwargs(root_id))
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert unflattened == [ inject_root_id(root_id, {
            'testA': [{'id': '2', 'testB': '3'}]
        }) ]
        # We expect no warnings
        assert recwarn.list == []

    def test_all_empty(self, root_id):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    inject_root_id(root_id, {
                        'id:integer': '',
                        'testA:number': '',
                        'testB:boolean': '',
                        'testC:array': '',
                        'testD:string': '',
                    }, '')
                ]
            },
            main_sheet_name='custom_main',
            **root_id_kwargs(root_id))
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 0

    def test_types_empty(self, root_id):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    inject_root_id(root_id, {
                        'id:integer': '',
                        'testA:number': '',
                        'testB:boolean': '',
                        'testC:array': '',
                        'testD:string': '',
                        'testE': '',
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_kwargs(root_id))
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 1
        assert output[0] == inject_root_id(root_id, {})


