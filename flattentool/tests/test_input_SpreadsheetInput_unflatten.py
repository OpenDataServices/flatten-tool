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

class RootIDHelper(object):
    def __init__(self, root_id):
        self.root_id = root_id
        self.kwargs = {'root_id': root_id} if root_id is not None else {}
        
    def inject(self, d, value=None):
        d.update({'ocid' if self.root_id is None else self.root_id: value if value is not None else 1})
        return d

    def __repr__(self):
        return '<RootIDHelper(root_id={})>'.format(self.root_id)

@pytest.fixture(scope='module', params=[None, 'custom', ''])
def root_id_helper(request):
    return RootIDHelper(request.param)

class TestUnflatten(object):
    def test_main_sheet_flat(self, root_id_helper):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    root_id_helper.inject({
                        'id': 2,
                        'testA': 3,
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_helper.kwargs)
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            root_id_helper.inject({'id': 2, 'testA': 3})
        ]

    def test_main_sheet_nonflat(self, root_id_helper):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    root_id_helper.inject({
                        'id': 2,
                        'testA/testB': 3,
                        'testA/testC': 4,
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_helper.kwargs)
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            root_id_helper.inject({'id': 2, 'testA': {'testB': 3, 'testC': 4}})
        ]

    def test_unicode(self, root_id_helper):
        unicode_string = 'éαГ😼𝒞人'
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    root_id_helper.inject({
                        'testA': unicode_string,
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_helper.kwargs)
        spreadsheet_input.read_sheets()
        assert list(spreadsheet_input.unflatten()) == [
            root_id_helper.inject({'testA': unicode_string})
        ]


class TestUnflattenRollup(object):
    def test_rollup(self, recwarn, root_id_helper):
        spreadsheet_input = ListInput(
            sheets={
                'main': [
                    root_id_helper.inject({
                        'id': 2,
                        'testA[]/id': 3,
                        'testA[]/testB': 4
                    })
                ]
            },
            main_sheet_name='main',
            **root_id_helper.kwargs
        )
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert unflattened == [
            root_id_helper.inject({'id': 2, 'testA': [{'id': 3, 'testB': 4}]})
        ]
        # We expect no warnings
        assert recwarn.list == []

    def test_rollup_no_id(self, recwarn, root_id_helper):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    root_id_helper.inject({
                        'testA[]/id': '2',
                        'testA[]/testB': '3',
                    })
                ]
            },
            main_sheet_name='custom_main',
            **root_id_helper.kwargs)
        spreadsheet_input.read_sheets()
        unflattened = list(spreadsheet_input.unflatten())
        assert len(unflattened) == 1
        assert unflattened == [ root_id_helper.inject({
            'testA': [{'id': '2', 'testB': '3'}]
        }) ]
        # We expect no warnings
        assert recwarn.list == []



class TestUnflattenEmpty(object):
    def test_all_empty(self, root_id_helper):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    root_id_helper.inject({
                        'id:integer': '',
                        'testA:number': '',
                        'testB:boolean': '',
                        'testC:array': '',
                        'testD:string': '',
                    }, '')
                ]
            },
            main_sheet_name='custom_main',
            **root_id_helper.kwargs)
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 0

    def test_types_empty(self, root_id_helper):
        spreadsheet_input = ListInput(
            sheets={
                'custom_main': [
                    root_id_helper.inject({
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
            **root_id_helper.kwargs)
        spreadsheet_input.read_sheets()
        output = list(spreadsheet_input.unflatten())
        assert len(output) == 1
        assert output[0] == root_id_helper.inject({})


