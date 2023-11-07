# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
from collections import OrderedDict
from decimal import Decimal

import pytest

from flattentool.json_input import (
    BadlyFormedJSONError,
    BadlyFormedJSONErrorUTF8,
    JSONParser,
)
from flattentool.schema import SchemaParser
from flattentool.tests.test_schema_parser import object_in_array_example_properties


def listify(d):
    return {k: list(v) for k, v in d.items()}


def test_jsonparser_bad_json(tmpdir):
    test_json = tmpdir.join("test.json")
    test_json.write('{"a":"b",}')
    with pytest.raises(BadlyFormedJSONError):
        JSONParser(json_filename=test_json.strpath)
    # matches against Python base error type
    with pytest.raises(ValueError):
        JSONParser(json_filename=test_json.strpath)


def test_jsonparser_bad_json_utf8():
    name = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "fixtures", "bad-utf8.json"
    )
    # matches against the special error type
    with pytest.raises(BadlyFormedJSONErrorUTF8):
        JSONParser(json_filename=name)
    # matches against our base error type
    with pytest.raises(BadlyFormedJSONError):
        JSONParser(json_filename=name)
    # matches against Python base error type
    with pytest.raises(ValueError):
        JSONParser(json_filename=name)


def test_jsonparser_arguments_exceptions(tmpdir):
    """
    Test that JSONParser throws a ValueError if it receives too many or too few arguments.

    """
    test_json = tmpdir.join("test.json")
    test_json.write("{}")
    with pytest.raises(ValueError):
        JSONParser()
    with pytest.raises(ValueError):
        JSONParser(json_filename=test_json.strpath, root_json_dict={})


def test_json_filename(tmpdir):
    test_json = tmpdir.join("test.json")
    test_json.write('[{"a":"b"}]')
    parser = JSONParser(json_filename=test_json.strpath)
    assert list(parser.main_sheet.lines) == [{"a": "b"}]


def test_json_filename_utf8(tmpdir):
    test_json = tmpdir.join("test.json")
    test_json.write_text('[{"a":"éαГ😼𝒞人"}]', encoding="utf-8")
    parser = JSONParser(json_filename=test_json.strpath)
    assert list(parser.main_sheet.lines) == [{"a": "éαГ😼𝒞人"}]


def test_json_filename_ordered(tmpdir):
    test_json = tmpdir.join("test.json")
    test_json.write('[{"a":"b", "c": "d"}]')
    parser = JSONParser(json_filename=test_json.strpath)
    assert list(parser.main_sheet.lines) == [{"a": "b", "c": "d"}]


def test_parse_empty_json_dict():
    parser = JSONParser(root_json_dict={})
    assert list(parser.main_sheet) == []
    assert list(parser.main_sheet.lines) == []
    assert parser.sub_sheets == {}


def test_parse_basic_json_dict():
    parser = JSONParser(
        root_json_dict=[
            OrderedDict(
                [
                    ("a", "b"),
                    ("c", "d"),
                ]
            ),
            OrderedDict(
                [
                    ("a", "e"),
                    ("c", "f"),
                ]
            ),
        ]
    )
    assert list(parser.main_sheet) == ["a", "c"]
    assert list(parser.main_sheet.lines) == [
        {"a": "b", "c": "d"},
        {"a": "e", "c": "f"},
    ]
    assert parser.sub_sheets == {}


def test_parse_nested_dict_json_dict():
    parser = JSONParser(
        root_json_dict=[
            OrderedDict(
                [
                    ("a", "b"),
                    ("c", OrderedDict([("d", "e")])),
                ]
            )
        ]
    )
    assert list(parser.main_sheet) == ["a", "c/d"]
    assert list(parser.main_sheet.lines) == [{"a": "b", "c/d": "e"}]
    assert parser.sub_sheets == {}


def test_parse_nested_list_json_dict():
    parser = JSONParser(
        root_json_dict=[
            OrderedDict(
                [
                    ("a", "b"),
                    ("c", [OrderedDict([("d", "e")])]),
                ]
            )
        ]
    )
    assert list(parser.main_sheet) == ["a"]
    assert list(parser.main_sheet.lines) == [{"a": "b"}]
    assert listify(parser.sub_sheets) == {"c": ["c/0/d"]}
    assert list(parser.sub_sheets["c"].lines) == [{"c/0/d": "e"}]


def test_parse_array():
    parser = JSONParser(
        root_json_dict=[OrderedDict([("testarray", ["item", "anotheritem", 42])])]
    )
    assert list(parser.main_sheet) == ["testarray"]
    assert list(parser.main_sheet.lines) == [{"testarray": "item;anotheritem;42"}]
    assert parser.sub_sheets == {}


def test_parse_array_of_arrays():
    parser = JSONParser(
        root_json_dict=[
            OrderedDict([("testarray", [["item", "anotheritem", 42], ["a", "b", 1]])])
        ]
    )
    assert list(parser.main_sheet) == ["testarray"]
    assert list(parser.main_sheet.lines) == [{"testarray": "item,anotheritem,42;a,b,1"}]
    assert parser.sub_sheets == {}


def test_root_list_path():
    parser = JSONParser(
        root_json_dict={
            "custom_key": [
                OrderedDict(
                    [
                        ("a", "b"),
                        ("c", "d"),
                    ]
                )
            ]
        },
        root_list_path="custom_key",
    )
    assert list(parser.main_sheet) == ["a", "c"]
    assert list(parser.main_sheet.lines) == [{"a": "b", "c": "d"}]
    assert parser.sub_sheets == {}


class TestParseIDs(object):
    def test_parse_ids(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("ocid", 1),
                        ("id", 2),
                        ("a", "b"),
                        (
                            "c",
                            [
                                OrderedDict([("id", 3), ("d", "e")]),
                                OrderedDict([("id", 3), ("d", "e2")]),
                            ],
                        ),
                        (
                            "f",
                            {"g": "h"},
                        ),  # Check that having nested objects doesn't break ID output
                    ]
                )
            ],
            root_id="ocid",
        )
        assert list(parser.main_sheet) == ["ocid", "id", "a", "f/g"]
        assert list(parser.main_sheet.lines) == [
            {"ocid": 1, "id": 2, "a": "b", "f/g": "h"}
        ]
        assert listify(parser.sub_sheets) == {"c": ["ocid", "id", "c/0/id", "c/0/d"]}
        assert list(parser.sub_sheets["c"].lines) == [
            {"ocid": 1, "id": 2, "c/0/id": 3, "c/0/d": "e"},
            {"ocid": 1, "id": 2, "c/0/id": 3, "c/0/d": "e2"},
        ]

    def test_parse_ids_subsheet(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("ocid", 1),
                        ("id", 2),
                        (
                            "testnest",
                            [
                                OrderedDict(
                                    [
                                        ("id", 3),
                                        ("a", "b"),
                                        (
                                            "c",
                                            [
                                                OrderedDict([("d", "e")]),
                                                OrderedDict([("d", "e2")]),
                                            ],
                                        ),
                                        (
                                            "f",
                                            {"g": "h"},
                                        ),  # Check that having nested objects doesn't break ID output
                                    ]
                                )
                            ],
                        ),
                    ]
                )
            ],
            root_id="ocid",
        )
        assert list(parser.main_sheet) == ["ocid", "id"]
        assert list(parser.main_sheet.lines) == [
            {
                "ocid": 1,
                "id": 2,
            }
        ]
        assert listify(parser.sub_sheets) == {
            "testnest": [
                "ocid",
                "id",
                "testnest/0/id",
                "testnest/0/a",
                "testnest/0/f/g",
            ],
            "tes_c": ["ocid", "id", "testnest/0/id", "testnest/0/c/0/d"],
        }
        assert list(parser.sub_sheets["testnest"].lines) == [
            {
                "ocid": 1,
                "id": 2,
                "testnest/0/id": 3,
                "testnest/0/a": "b",
                "testnest/0/f/g": "h",
            },
        ]
        assert list(parser.sub_sheets["tes_c"].lines) == [
            {"ocid": 1, "id": 2, "testnest/0/id": 3, "testnest/0/c/0/d": "e"},
            {"ocid": 1, "id": 2, "testnest/0/id": 3, "testnest/0/c/0/d": "e2"},
        ]

    def test_parse_ids_nested(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("ocid", 1),
                        ("id", 2),
                        ("a", "b"),
                        (
                            "testnest",
                            OrderedDict(
                                [
                                    ("id", 3),
                                    (
                                        "c",
                                        [
                                            OrderedDict([("d", "e")]),
                                            OrderedDict([("d", "e2")]),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                        (
                            "f",
                            {"g": "h"},
                        ),  # Check that having nested objects doesn't break ID output
                    ]
                )
            ],
            root_id="ocid",
        )
        assert list(parser.main_sheet) == ["ocid", "id", "a", "testnest/id", "f/g"]
        assert list(parser.main_sheet.lines) == [
            {"ocid": 1, "id": 2, "a": "b", "testnest/id": 3, "f/g": "h"}
        ]
        assert listify(parser.sub_sheets) == {
            "tes_c": ["ocid", "id", "testnest/id", "testnest/c/0/d"]
        }
        assert list(parser.sub_sheets["tes_c"].lines) == [
            {"ocid": 1, "id": 2, "testnest/id": 3, "testnest/c/0/d": "e"},
            {"ocid": 1, "id": 2, "testnest/id": 3, "testnest/c/0/d": "e2"},
        ]


class TestParseUsingSchema(object):
    @pytest.mark.parametrize("remove_empty_schema_columns", [False, True])
    def test_sub_sheets(self, tmpdir, remove_empty_schema_columns):
        test_schema = tmpdir.join("test.json")
        test_schema.write(
            """{
            "properties": {
                "c": {
                    "type": "array",
                    "items": {"$ref": "#/testB"}
                },
                "g": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "h": { "type": "string"}
                        }
                    }
                }
            },
            "testB": {
                "type": "object",
                "properties": {
                    "d": { "type": "string" },
                    "f": { "type": "string" }
                }
            }
        }"""
        )
        schema_parser = SchemaParser(
            schema_filename=test_schema.strpath, root_id="ocid"
        )
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("a", "b"),
                        ("c", [OrderedDict([("d", "e")])]),
                    ]
                )
            ],
            schema_parser=schema_parser,
            remove_empty_schema_columns=remove_empty_schema_columns,
        )
        assert list(parser.main_sheet) == ["a"]
        assert list(parser.main_sheet.lines) == [{"a": "b"}]
        assert len(parser.sub_sheets) == 2 if not remove_empty_schema_columns else 1
        if not remove_empty_schema_columns:
            assert list(parser.sub_sheets["c"]) == list(["ocid", "c/0/d", "c/0/f"])
            assert list(parser.sub_sheets["g"]) == list(["ocid", "g/0/h"])
        else:
            assert list(parser.sub_sheets["c"]) == list(["ocid", "c/0/d"])
        assert parser.sub_sheets["c"].lines == [{"c/0/d": "e"}]

    def test_column_matching(self, tmpdir):
        test_schema = tmpdir.join("test.json")
        test_schema.write(
            """{
            "properties": {
                "c": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }"""
        )
        schema_parser = SchemaParser(schema_filename=test_schema.strpath)
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("c", ["d"]),
                    ]
                )
            ],
            schema_parser=schema_parser,
        )
        assert list(parser.main_sheet) == ["c"]
        assert list(parser.main_sheet.lines) == [{"c": "d"}]
        assert len(parser.sub_sheets) == 0

    def test_rollup(self):
        schema_parser = SchemaParser(
            root_schema_dict={
                "properties": {
                    "testA": {
                        "type": "array",
                        "rollUp": ["testB"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "testB": {"type": "string"},
                                "testC": {"type": "string"},
                            },
                        },
                    },
                }
            },
            rollup=True,
            root_id="ocid",
        )
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("testA", [OrderedDict([("testB", "1"), ("testC", "2")])]),
                    ]
                )
            ],
            schema_parser=schema_parser,
            root_id="ocid",
            rollup=True,
        )
        assert list(parser.main_sheet) == ["testA/0/testB"]
        assert list(parser.main_sheet.lines) == [{"testA/0/testB": "1"}]
        assert len(parser.sub_sheets) == 1
        assert set(parser.sub_sheets["testA"]) == set(
            ["ocid", "testA/0/testB", "testA/0/testC"]
        )
        assert parser.sub_sheets["testA"].lines == [
            {"testA/0/testB": "1", "testA/0/testC": "2"}
        ]

    def test_rollup_multiple_values(self, recwarn):
        schema_parser = SchemaParser(
            root_schema_dict={
                "properties": {
                    "testA": {
                        "type": "array",
                        "rollUp": ["testB"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "testB": {"type": "string"},
                                "testC": {"type": "string"},
                            },
                        },
                    },
                }
            },
            rollup=True,
        )
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        (
                            "testA",
                            [
                                OrderedDict([("testB", "1"), ("testC", "2")]),
                                OrderedDict([("testB", "3"), ("testC", "4")]),
                            ],
                        ),
                    ]
                )
            ],
            schema_parser=schema_parser,
            rollup=True,
        )
        assert list(parser.main_sheet) == ["testA/0/testB"]
        assert list(parser.main_sheet.lines) == [
            {
                "testA/0/testB": "WARNING: More than one value supplied, consult the relevant sub-sheet for the data."
            }
        ]
        assert len(parser.sub_sheets) == 1
        assert set(parser.sub_sheets["testA"]) == set(
            ["testA/0/testB", "testA/0/testC"]
        )
        assert parser.sub_sheets["testA"].lines == [
            {"testA/0/testB": "1", "testA/0/testC": "2"},
            {"testA/0/testB": "3", "testA/0/testC": "4"},
        ]
        w = recwarn.pop(UserWarning)
        assert "Could not provide rollup" in str(w.message)

    def test_two_parents(self):
        # This is a copy of test_two_parents from test_schema_parser.py, in
        # order to check that flattening and template generation use the same
        # sheet names
        schema_parser = SchemaParser(
            root_schema_dict={
                "properties": OrderedDict(
                    [
                        (
                            "Atest",
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": object_in_array_example_properties(
                                        "Btest", "Ctest"
                                    ),
                                },
                            },
                        ),
                        (
                            "Dtest",
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": object_in_array_example_properties(
                                        "Btest", "Etest"
                                    ),
                                },
                            },
                        ),
                    ]
                )
            }
        )
        schema_parser.parse()
        parser = JSONParser(
            root_json_dict=[
                {
                    "Atest": [{"id": 1, "Btest": [{"Ctest": 2}]}],
                    "Dtest": [{"id": 3, "Btest": [{"Etest": 4}]}],
                }
            ],
            schema_parser=schema_parser,
        )
        assert set(parser.main_sheet) == set()
        assert set(parser.sub_sheets) == set(
            ["Atest", "Dtest", "Ate_Btest", "Dte_Btest"]
        )
        assert list(parser.sub_sheets["Atest"]) == ["Atest/0/id"]
        assert list(parser.sub_sheets["Dtest"]) == ["Dtest/0/id"]
        assert list(parser.sub_sheets["Ate_Btest"]) == [
            "Atest/0/id",
            "Atest/0/Btest/0/Ctest",
        ]
        assert list(parser.sub_sheets["Dte_Btest"]) == [
            "Dtest/0/id",
            "Dtest/0/Btest/0/Etest",
        ]


# TODO Check support for decimals, integers, booleans and Nones


class TestParseIDsCustomRootID(object):
    def test_parse_ids(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("custom", 1),
                        ("id", 2),
                        ("a", "b"),
                        (
                            "c",
                            [
                                OrderedDict([("id", 3), ("d", "e")]),
                                OrderedDict([("id", 3), ("d", "e2")]),
                            ],
                        ),
                        (
                            "f",
                            {"g": "h"},
                        ),  # Check that having nested objects doesn't break ID output
                    ]
                )
            ],
            root_id="custom",
        )
        assert list(parser.main_sheet) == ["custom", "id", "a", "f/g"]
        assert list(parser.main_sheet.lines) == [
            {"custom": 1, "id": 2, "a": "b", "f/g": "h"}
        ]
        assert listify(parser.sub_sheets) == {"c": ["custom", "id", "c/0/id", "c/0/d"]}
        assert list(parser.sub_sheets["c"].lines) == [
            {"custom": 1, "id": 2, "c/0/id": 3, "c/0/d": "e"},
            {"custom": 1, "id": 2, "c/0/id": 3, "c/0/d": "e2"},
        ]

    def test_parse_ids_subsheet(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("custom", 1),
                        ("id", 2),
                        (
                            "testnest",
                            [
                                OrderedDict(
                                    [
                                        ("id", 3),
                                        ("a", "b"),
                                        (
                                            "c",
                                            [
                                                OrderedDict([("d", "e")]),
                                                OrderedDict([("d", "e2")]),
                                            ],
                                        ),
                                        (
                                            "f",
                                            {"g": "h"},
                                        ),  # Check that having nested objects doesn't break ID output
                                    ]
                                )
                            ],
                        ),
                    ]
                )
            ],
            root_id="custom",
        )
        assert list(parser.main_sheet) == ["custom", "id"]
        assert list(parser.main_sheet.lines) == [
            {
                "custom": 1,
                "id": 2,
            }
        ]
        assert listify(parser.sub_sheets) == {
            "testnest": [
                "custom",
                "id",
                "testnest/0/id",
                "testnest/0/a",
                "testnest/0/f/g",
            ],
            "tes_c": ["custom", "id", "testnest/0/id", "testnest/0/c/0/d"],
        }
        assert list(parser.sub_sheets["testnest"].lines) == [
            {
                "custom": 1,
                "id": 2,
                "testnest/0/id": 3,
                "testnest/0/a": "b",
                "testnest/0/f/g": "h",
            },
        ]
        assert list(parser.sub_sheets["tes_c"].lines) == [
            {"custom": 1, "id": 2, "testnest/0/id": 3, "testnest/0/c/0/d": "e"},
            {"custom": 1, "id": 2, "testnest/0/id": 3, "testnest/0/c/0/d": "e2"},
        ]

    def test_parse_ids_nested(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("custom", 1),
                        ("id", 2),
                        ("a", "b"),
                        (
                            "testnest",
                            OrderedDict(
                                [
                                    ("id", 3),
                                    (
                                        "c",
                                        [
                                            OrderedDict([("d", "e")]),
                                            OrderedDict([("d", "e2")]),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                        (
                            "f",
                            {"g": "h"},
                        ),  # Check that having nested objects doesn't break ID output
                    ]
                )
            ],
            root_id="custom",
        )
        assert list(parser.main_sheet) == ["custom", "id", "a", "testnest/id", "f/g"]
        assert list(parser.main_sheet.lines) == [
            {"custom": 1, "id": 2, "a": "b", "testnest/id": 3, "f/g": "h"}
        ]
        assert listify(parser.sub_sheets) == {
            "tes_c": ["custom", "id", "testnest/id", "testnest/c/0/d"]
        }
        assert list(parser.sub_sheets["tes_c"].lines) == [
            {"custom": 1, "id": 2, "testnest/id": 3, "testnest/c/0/d": "e"},
            {"custom": 1, "id": 2, "testnest/id": 3, "testnest/c/0/d": "e2"},
        ]


class TestParseIDsNoRootID(object):
    def test_parse_ids(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("id", 2),
                        ("a", "b"),
                        (
                            "c",
                            [
                                OrderedDict([("id", 3), ("d", "e")]),
                                OrderedDict([("id", 3), ("d", "e2")]),
                            ],
                        ),
                        (
                            "f",
                            {"g": "h"},
                        ),  # Check that having nested objects doesn't break ID output
                    ]
                )
            ],
            root_id="",
        )
        assert list(parser.main_sheet) == ["id", "a", "f/g"]
        assert list(parser.main_sheet.lines) == [{"id": 2, "a": "b", "f/g": "h"}]
        assert listify(parser.sub_sheets) == {"c": ["id", "c/0/id", "c/0/d"]}
        assert list(parser.sub_sheets["c"].lines) == [
            {"id": 2, "c/0/id": 3, "c/0/d": "e"},
            {"id": 2, "c/0/id": 3, "c/0/d": "e2"},
        ]

    def test_parse_ids_subsheet(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("id", 2),
                        (
                            "testnest",
                            [
                                OrderedDict(
                                    [
                                        ("id", 3),
                                        ("a", "b"),
                                        (
                                            "c",
                                            [
                                                OrderedDict([("d", "e")]),
                                                OrderedDict([("d", "e2")]),
                                            ],
                                        ),
                                        (
                                            "f",
                                            {"g": "h"},
                                        ),  # Check that having nested objects doesn't break ID output
                                    ]
                                )
                            ],
                        ),
                    ]
                )
            ],
            root_id="",
        )
        assert list(parser.main_sheet) == ["id"]
        assert list(parser.main_sheet.lines) == [
            {
                "id": 2,
            }
        ]
        assert listify(parser.sub_sheets) == {
            "testnest": ["id", "testnest/0/id", "testnest/0/a", "testnest/0/f/g"],
            "tes_c": ["id", "testnest/0/id", "testnest/0/c/0/d"],
        }
        assert list(parser.sub_sheets["testnest"].lines) == [
            {
                "id": 2,
                "testnest/0/id": 3,
                "testnest/0/a": "b",
                "testnest/0/f/g": "h",
            },
        ]
        assert list(parser.sub_sheets["tes_c"].lines) == [
            {"id": 2, "testnest/0/id": 3, "testnest/0/c/0/d": "e"},
            {"id": 2, "testnest/0/id": 3, "testnest/0/c/0/d": "e2"},
        ]

    def test_parse_ids_nested(self):
        parser = JSONParser(
            root_json_dict=[
                OrderedDict(
                    [
                        ("id", 2),
                        ("a", "b"),
                        (
                            "testnest",
                            OrderedDict(
                                [
                                    ("id", 3),
                                    (
                                        "c",
                                        [
                                            OrderedDict([("d", "e")]),
                                            OrderedDict([("d", "e2")]),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                        (
                            "f",
                            {"g": "h"},
                        ),  # Check that having nested objects doesn't break ID output
                    ]
                )
            ],
            root_id="",
        )
        assert list(parser.main_sheet) == ["id", "a", "testnest/id", "f/g"]
        assert list(parser.main_sheet.lines) == [
            {"id": 2, "a": "b", "testnest/id": 3, "f/g": "h"}
        ]
        assert listify(parser.sub_sheets) == {
            "tes_c": ["id", "testnest/id", "testnest/c/0/d"]
        }
        assert list(parser.sub_sheets["tes_c"].lines) == [
            {"id": 2, "testnest/id": 3, "testnest/c/0/d": "e"},
            {"id": 2, "testnest/id": 3, "testnest/c/0/d": "e2"},
        ]


@pytest.mark.geo
def test_parse_geojson():
    parser = JSONParser(
        root_json_dict=[
            {
                "a": "b",
                "c": [
                    {
                        "d": {
                            "type": "Point",
                            "coordinates": [Decimal("53.486434"), Decimal("-2.239353")],
                        }
                    },
                    {
                        "d": {
                            "type": "LineString",
                            "coordinates": [
                                [Decimal("-0.173"), Decimal("5.626")],
                                [Decimal("-0.178"), Decimal("5.807")],
                                [Decimal("-0.112"), Decimal("5.971")],
                                [Decimal("-0.211"), Decimal("5.963")],
                                [Decimal("-0.321"), Decimal("6.17")],
                                [Decimal("-0.488"), Decimal("6.29")],
                                [Decimal("-0.560"), Decimal("6.421")],
                                [Decimal("-0.752"), Decimal("6.533")],
                                [Decimal("-0.867"), Decimal("6.607")],
                                [Decimal("-1.101"), Decimal("6.585")],
                                [Decimal("-1.304"), Decimal("6.623")],
                                [Decimal("-1.461"), Decimal("6.727")],
                                [Decimal("-1.628"), Decimal("6.713")],
                            ],
                        }
                    },
                ],
            }
        ],
        convert_flags={"wkt": True},
    )
    assert list(parser.main_sheet) == ["a"]
    assert list(parser.main_sheet.lines) == [{"a": "b"}]
    assert listify(parser.sub_sheets) == {"c": ["c/0/d"]}
    assert list(parser.sub_sheets["c"].lines) == [
        {"c/0/d": "POINT (53.486434 -2.239353)"},
        {
            "c/0/d": "LINESTRING (-0.173 5.626, -0.178 5.807, -0.112 5.971, -0.211 5.963, -0.321 6.17, -0.488 6.29, -0.56 6.421, -0.752 6.533, -0.867 6.607, -1.101 6.585, -1.304 6.623, -1.461 6.727, -1.628 6.713)"
        },
    ]


@pytest.mark.geo
def test_parse_bad_geojson(recwarn):
    parser = JSONParser(
        root_json_dict=[
            {
                "a": "b",
                "c": [
                    {
                        "d": {
                            "type": "test",
                            "coordinates": [],
                        }
                    },
                    {
                        "d": {
                            "type": "Point",
                            "coordinates": [],
                        }
                    },
                    {
                        "d": {
                            "type": "Point",
                            "coordinates": "test",
                        }
                    },
                    {
                        "d": {
                            "type": "Point",
                            "coordinates": 3,
                        }
                    },
                    {
                        "d": {
                            "type": "Point",
                            "coordinates": [Decimal("53.486434")],
                        }
                    },
                    {
                        "d": {
                            "type": "LineString",
                            "coordinates": [
                                [Decimal("-0.173"), Decimal("5.626")],
                                [Decimal("-0.178")],
                                [Decimal("-0.112"), Decimal("5.971")],
                            ],
                        }
                    },
                ],
            }
        ],
        convert_flags={"wkt": True},
    )
    assert list(parser.main_sheet) == ["a"]
    assert list(parser.main_sheet.lines) == [{"a": "b"}]
    assert listify(parser.sub_sheets) == {"c": ["c/0/d"]}
    assert list(parser.sub_sheets["c"].lines) == [
        {},
        {"c/0/d": "POINT EMPTY"},
        {},
        {},
        {},
        {},
    ]
    w = recwarn.pop(UserWarning)
    assert (
        str(w.message)
        == "Invalid GeoJSON: GeometryTypeError(\"Unknown geometry type: 'test'\")"
    )
    w = recwarn.pop(UserWarning)
    assert str(w.message) == "Invalid GeoJSON: TypeError('iteration over a 0-d array')"
    w = recwarn.pop(UserWarning)
    assert (
        str(w.message) == "Invalid GeoJSON: TypeError(\"'int' object is not iterable\")"
    )
    w = recwarn.pop(UserWarning)
    # There are different warning messages for Python versions before 3.8. This
    # is because an old version of numpy is installed (the last compatible with
    # these versions of Python), which has different messages.
    if sys.version_info < (3, 8):
        assert (
            str(w.message)
            == "Creating an ndarray from ragged nested sequences (which is a list-or-tuple of lists-or-tuples-or ndarrays with different lengths or shapes) is deprecated. If you meant to do this, you must specify 'dtype=object' when creating the ndarray."
        )
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message)
            == "Invalid GeoJSON: ValueError('linestrings: Input operand 0 does not have enough dimensions (has 1, gufunc core with signature (i, d)->() requires 2)')"
        )
    else:
        assert (
            str(w.message)
            == "Invalid GeoJSON: ValueError('setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (3,) + inhomogeneous part.')"
        )
    assert len(recwarn.list) == 0


def test_parse_geojson_wkt_off():
    parser = JSONParser(
        root_json_dict=[
            {
                "a": "b",
                "c": [
                    {
                        "d": {
                            "type": "Point",
                            "coordinates": [Decimal("53.486434"), Decimal("-2.239353")],
                        }
                    },
                    {
                        "d": {
                            "type": "LineString",
                            "coordinates": [
                                [Decimal("-0.173"), Decimal("5.626")],
                                [Decimal("-0.178"), Decimal("5.807")],
                                [Decimal("-0.112"), Decimal("5.971")],
                                [Decimal("-0.211"), Decimal("5.963")],
                                [Decimal("-0.321"), Decimal("6.17")],
                                [Decimal("-0.488"), Decimal("6.29")],
                                [Decimal("-0.560"), Decimal("6.421")],
                                [Decimal("-0.752"), Decimal("6.533")],
                                [Decimal("-0.867"), Decimal("6.607")],
                                [Decimal("-1.101"), Decimal("6.585")],
                                [Decimal("-1.304"), Decimal("6.623")],
                                [Decimal("-1.461"), Decimal("6.727")],
                                [Decimal("-1.628"), Decimal("6.713")],
                            ],
                        }
                    },
                ],
            }
        ],
        convert_flags={"wkt": False},
    )
    assert list(parser.main_sheet) == ["a"]
    assert list(parser.main_sheet.lines) == [{"a": "b"}]
    assert listify(parser.sub_sheets) == {"c": ["c/0/d/type", "c/0/d/coordinates"]}
    assert list(parser.sub_sheets["c"].lines) == [
        {"c/0/d/type": "Point", "c/0/d/coordinates": "53.486434;-2.239353"},
        {
            "c/0/d/type": "LineString",
            "c/0/d/coordinates": "-0.173,5.626;-0.178,5.807;-0.112,5.971;-0.211,5.963;-0.321,6.17;-0.488,6.29;-0.560,6.421;-0.752,6.533;-0.867,6.607;-1.101,6.585;-1.304,6.623;-1.461,6.727;-1.628,6.713",
        },
    ]
