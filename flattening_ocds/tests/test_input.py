# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flattening_ocds.input import SpreadsheetInput, CSVInput, XLSXInput
from flattening_ocds.input import unflatten_line, unflatten_spreadsheet_input, \
    find_deepest_id_field, convert_type, path_search
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
from six import text_type


def test_spreadsheetinput_base_fails():
    spreadsheet_input = SpreadsheetInput()
    with pytest.raises(NotImplementedError):
        spreadsheet_input.read_sheets()
    with pytest.raises(NotImplementedError):
        spreadsheet_input.get_sheet_lines('test')


class TestSuccessfulInput(object):
    def test_csv_input(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write('colA,colB\ncell1,cell2\ncell3,cell4')
        subsheet = tmpdir.join('subsheet.csv')
        subsheet.write('colC,colD\ncell5,cell6\ncell7,cell8')

        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        assert csvinput.main_sheet_name == 'main'

        csvinput.read_sheets()

        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert csvinput.sub_sheet_names == ['subsheet']
        assert list(csvinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_input(self):
        xlsxinput = XLSXInput(input_name='flattening_ocds/tests/xlsx/basic.xlsx', main_sheet_name='main')
        assert xlsxinput.main_sheet_name == 'main'

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_main_sheet_lines()) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert xlsxinput.sub_sheet_names == ['subsheet']
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_input_integer(self):
        xlsxinput = XLSXInput(input_name='flattening_ocds/tests/xlsx/integer.xlsx', main_sheet_name='main')
        assert xlsxinput.main_sheet_name == 'main'

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_main_sheet_lines()) == \
            [{'colA': 1}]
        assert xlsxinput.sub_sheet_names == []


class TestInputFailure(object):
    def test_csv_no_directory(self):
        csvinput = CSVInput(input_name='nonesensedirectory', main_sheet_name='main')
        if sys.version > '3':
            with pytest.raises(FileNotFoundError):
                csvinput.read_sheets()
        else:
            with pytest.raises(OSError):
                csvinput.read_sheets()

    def test_csv_no_files(self, tmpdir):
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        with pytest.raises(ValueError) as e:
            csvinput.read_sheets()
        assert 'Main sheet' in text_type(e) and 'not found' in text_type(e)

    def test_xlsx_no_file(self, tmpdir):
        xlsxinput = XLSXInput(input_name=tmpdir.strpath.join('test.xlsx'), main_sheet_name='main')
        with pytest.raises(openpyxl.exceptions.InvalidFileException):
            xlsxinput.read_sheets()

    def test_xlsx_no_main_sheet(self):
        xlsxinput = XLSXInput(input_name='flattening_ocds/tests/xlsx/basic.xlsx', main_sheet_name='notmain')
        with pytest.raises(ValueError) as e:
            xlsxinput.read_sheets()
        assert 'Main sheet "notmain" not found in workbook.' in text_type(e)


class TestUnicodeInput(object):
    def test_csv_input_utf8(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\néαГ😼𝒞人', encoding='utf8')
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')  # defaults to utf8
        csvinput.read_sheets()
        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'éαГ😼𝒞人'}]
        assert csvinput.sub_sheet_names == []

    def test_csv_input_latin1(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\né', encoding='latin-1')
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        csvinput.encoding = 'latin-1'
        csvinput.read_sheets()
        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'é'}]
        assert csvinput.sub_sheet_names == []

    @pytest.mark.xfail(
        sys.version_info < (3, 0),
        reason='Python 2 CSV readers does not support UTF-16 (or any encodings with null bytes')
    def test_csv_input_utf16(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\néαГ😼𝒞人', encoding='utf16')
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        csvinput.encoding = 'utf16'
        csvinput.read_sheets()
        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'éαГ😼𝒞人'}]
        assert csvinput.sub_sheet_names == []

    def test_xlsx_input_utf8(self):
        """This is an xlsx file saved by OpenOffice. It seems to use UTF8 internally."""
        xlsxinput = XLSXInput(input_name='flattening_ocds/tests/xlsx/unicode.xlsx', main_sheet_name='main')

        xlsxinput.read_sheets()
        assert list(xlsxinput.get_main_sheet_lines())[0]['id'] == 'éαГ😼𝒞人'


class ListInput(SpreadsheetInput):
    def __init__(self, sheets, **kwargs):
        self.sheets = sheets
        super(ListInput, self).__init__(**kwargs)

    def get_sheet_lines(self, sheet_name):
        return self.sheets[sheet_name]

    def read_sheets(self):
        self.sub_sheet_names = list(self.sheets.keys())
        self.sub_sheet_names.remove(self.main_sheet_name)


def test_unflatten_line():
    # Check flat fields remain flat
    assert unflatten_line({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    assert unflatten_line({'a/b': 1, 'a/c': 2, 'd/e': 3}) == {'a': {'b': 1, 'c': 2}, 'd': {'e': 3}}
    # Check more than two levels of nesting, and that multicharacter fields aren't broken
    assert unflatten_line({'fieldA/b/c/d': 'value'}) == {'fieldA': {'b': {'c': {'d': 'value'}}}}


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


def test_find_deepest_id_field():
    assert find_deepest_id_field(['a/b/id', 'a/b/c/id']) == 'a/b/c/id'
    with pytest.raises(ValueError):
        find_deepest_id_field(['a/b/id', 'c/id'])


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
        assert list(unflatten_spreadsheet_input(spreadsheet_input)) == [
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
        assert list(unflatten_spreadsheet_input(spreadsheet_input)) == [
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
        assert list(unflatten_spreadsheet_input(spreadsheet_input)) == [
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
        assert list(unflatten_spreadsheet_input(spreadsheet_input)) == [
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
        unflattened = list(unflatten_spreadsheet_input(spreadsheet_input))
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
        assert list(unflatten_spreadsheet_input(spreadsheet_input)) == [
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
        unflattened = list(unflatten_spreadsheet_input(spreadsheet_input))
        # We should have a warning about conflicting ID fields
        w = recwarn.pop(UserWarning)
        assert 'Multiple conflicting ID fields' in text_type(w.message)
        # (line number includes an assumed header line)
        assert 'line 2 of sheet sub' in text_type(w.message)
        # Only one top level object should have been outputted
        assert len(unflattened) == 1
        # Check that the valid data is outputted correctly
        assert unflatten_spreadsheet_input(spreadsheet_input)[0] == \
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
        assert list(unflatten_spreadsheet_input(spreadsheet_input)) == [
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
        unflattened = list(unflatten_spreadsheet_input(spreadsheet_input))
        # We should have a warning about conflicting ID fields
        w = recwarn.pop(UserWarning)
        assert 'no parent id fields populated' in text_type(w.message)
        assert 'Line 2 of sheet sub' in text_type(w.message)
        # Check that following lines are parsed correctly
        assert unflattened == [
            {'ocid': 1, 'id': 2, 'subField': [{'id': 3, 'testA': 5}]}
        ]


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
        output = list(unflatten_spreadsheet_input(spreadsheet_input))
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
        output = list(unflatten_spreadsheet_input(spreadsheet_input))
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
        output = list(unflatten_spreadsheet_input(spreadsheet_input))
        assert len(output) == 1
        assert output[0] == {'ocid': '1'}


def test_convert_type(recwarn):
    assert convert_type('', 'somestring') == 'somestring'
    # If not type is specified, ints are kept as ints...
    assert convert_type('', 3) == 3

    # ... but all other ojbects are converted to strings
    class NotAString(object):
        def __str__(self):
            return 'string representation'
    assert NotAString() != 'string representation'
    assert convert_type('', NotAString()) == 'string representation'
    assert convert_type('string', NotAString()) == 'string representation'

    assert convert_type('string', 3) == '3'
    assert convert_type('number', '3') == Decimal('3')
    assert convert_type('number', '1.2') == Decimal('1.2')
    assert convert_type('integer', '3') == 3
    assert convert_type('integer', 3) == 3

    assert convert_type('boolean', 'TRUE') is True
    assert convert_type('boolean', 'True') is True
    assert convert_type('boolean', 1) is True
    assert convert_type('boolean', '1') is True
    assert convert_type('boolean', 'FALSE') is False
    assert convert_type('boolean', 'False') is False
    assert convert_type('boolean', 0) is False
    assert convert_type('boolean', '0') is False
    convert_type('boolean', 2)
    assert 'Unrecognised value for boolean: "2"' in text_type(recwarn.pop(UserWarning).message)
    convert_type('boolean', 'test')
    assert 'Unrecognised value for boolean: "test"' in text_type(recwarn.pop(UserWarning).message)

    convert_type('integer', 'test')
    assert 'Non-integer value "test"' in text_type(recwarn.pop(UserWarning).message)

    convert_type('number', 'test')
    assert 'Non-numeric value "test"' in text_type(recwarn.pop(UserWarning).message)

    assert convert_type('string', '') is None
    assert convert_type('number', '') is None
    assert convert_type('integer', '') is None
    assert convert_type('array', '') is None
    assert convert_type('boolean', '') is None
    assert convert_type('string', None) is None
    assert convert_type('number', None) is None
    assert convert_type('integer', None) is None
    assert convert_type('array', None) is None
    assert convert_type('boolean', None) is None

    assert convert_type('array', 'one') == ['one']
    assert convert_type('array', 'one;two') == ['one', 'two']
    assert convert_type('array', 'one,two;three,four') == [['one', 'two'], ['three', 'four']]

    with pytest.raises(ValueError) as e:
        convert_type('notatype', 'test')
    assert 'Unrecognised type: "notatype"' in text_type(e)
