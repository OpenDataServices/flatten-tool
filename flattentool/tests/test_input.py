# -*- coding: utf-8 -*-
"""
Tests of functions in input.py
Tests of SpreadsheetInput class and its children are in test_input_SpreadsheetInput*.py
"""
from __future__ import unicode_literals
from flattentool.input import path_search
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime


def test_path_search():
    goal_dict = {}
    assert goal_dict is not {}  # following tests rely on this
    assert path_search(goal_dict, []) is goal_dict
    assert path_search(
        {'testA': goal_dict},
        ['testA']) is goal_dict
    assert path_search(
        {'a1': {'b1': {'c1': goal_dict}}},
        ['a1', 'b1', 'c1']) is goal_dict
    assert path_search(
        {'a1': {'b1': {'c1': goal_dict}}},
        ['a1', 'b1[]'],
        id_fields={'a1/b1[]/id': 'c1'}) is goal_dict
    assert path_search(
        {'a1': {'b1': {'c1': goal_dict}}},
        ['a1[]', 'c1'],
        id_fields={'a1[]/id': 'b1'}) is goal_dict
    # Top is always assumed to be an arary
    assert path_search(
        {'a1': {'b1': {'c1': goal_dict}}},
        ['a1', 'c1'],
        id_fields={'a1/id': 'b1'},
        top=True) is goal_dict
