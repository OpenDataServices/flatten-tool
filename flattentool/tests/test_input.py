# -*- coding: utf-8 -*-
"""
Tests of functions in input.py
Tests of SpreadsheetInput class and its children are in test_input_SpreadsheetInput*.py
"""
from __future__ import unicode_literals

import csv
import io
import sys

import pytest

from flattentool.input import NullCharacterFilter, path_search


def test_path_search():
    goal_dict = {}
    assert goal_dict is not {}  # following tests rely on this
    assert path_search(goal_dict, []) is goal_dict
    assert path_search({"testA": goal_dict}, ["testA"]) is goal_dict
    assert (
        path_search({"a1": {"b1": {"c1": goal_dict}}}, ["a1", "b1", "c1"]) is goal_dict
    )
    assert (
        path_search(
            {"a1": {"b1": {"c1": goal_dict}}},
            ["a1", "b1[]"],
            id_fields={"a1/b1[]/id": "c1"},
        )
        is goal_dict
    )
    assert (
        path_search(
            {"a1": {"b1": {"c1": goal_dict}}},
            ["a1[]", "c1"],
            id_fields={"a1[]/id": "b1"},
        )
        is goal_dict
    )
    # Top is always assumed to be an array
    assert (
        path_search(
            {"a1": {"b1": {"c1": goal_dict}}},
            ["a1", "c1"],
            id_fields={"a1/id": "b1"},
            top=True,
        )
        is goal_dict
    )


def test_null_character_filter():
    # https://bugs.python.org/issue27580
    if sys.version_info < (3, 11):
        with pytest.raises(Exception):
            next(csv.reader(io.StringIO("\0")))

    try:
        next(csv.reader(NullCharacterFilter(io.StringIO("\0"))))
    except Exception as e:
        pytest.fail(str(e))
