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


class TestUnflattenRollup(object):
    def test_rollup(self, recwarn):
        spreadsheet_input = ListInput(
            sheets={
                'main': [
                    {
                        'ocid': 1,
                        'id': 2,
                        'testA[]/id': 3,
                        'testA[]/testB': 4
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


# TODO: Is this doing the same as TestUnflattenRollup above?
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


# TODO: Should this be grouped with TestUnflattenRollup above?
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

