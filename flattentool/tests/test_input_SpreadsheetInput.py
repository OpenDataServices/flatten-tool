# -*- coding: utf-8 -*-
"""
Tests of SpreadsheetInput class from input.py, and its chidlren.
Tests of unflatten method are in test_input_SpreadsheetInput_unflatten.py
"""
from __future__ import unicode_literals
from flattentool.input import SpreadsheetInput, CSVInput, XLSXInput, ODSInput, convert_type
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime
import pytz

class ListInput(SpreadsheetInput):
    def __init__(self, sheets, **kwargs):
        self.sheets = sheets
        super(ListInput, self).__init__(**kwargs)

    def get_sheet_lines(self, sheet_name):
        return self.sheets[sheet_name]

    def read_sheets(self):
        self.sub_sheet_names = list(self.sheets.keys())

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

        csvinput = CSVInput(input_name=tmpdir.strpath)

        csvinput.read_sheets()

        assert csvinput.sub_sheet_names == ['main', 'subsheet']
        assert list(csvinput.get_sheet_lines('main')) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert list(csvinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_input(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/basic.xlsx')

        xlsxinput.read_sheets()

        assert xlsxinput.sub_sheet_names == ['main', 'subsheet']
        assert list(xlsxinput.get_sheet_lines('main')) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_ods_input(self):
        odsinput = ODSInput(input_name='flattentool/tests/fixtures/ods/basic.ods')

        odsinput.read_sheets()

        assert list(odsinput.sub_sheet_names) == ['main', 'subsheet']
        assert list(odsinput.get_sheet_lines('main')) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert list(odsinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_vertical(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/basic_transpose.xlsx', vertical_orientation=True)

        xlsxinput.read_sheets()

        assert xlsxinput.sub_sheet_names == ['main', 'subsheet']
        assert list(xlsxinput.get_sheet_lines('main')) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_ods_vertical(self):
        odsinput = ODSInput(input_name='flattentool/tests/fixtures/ods/basic_transpose.ods', vertical_orientation=True)

        odsinput.read_sheets()

        assert list(odsinput.sub_sheet_names) == ['main', 'subsheet']
        assert list(odsinput.get_sheet_lines('main')) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert list(odsinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_include_ignore(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/basic_meta.xlsx', 
                              include_sheets=['Meta'], vertical_orientation=True
                             )
        xlsxinput.read_sheets()
        assert xlsxinput.sub_sheet_names == ['Meta']
        assert list(xlsxinput.get_sheet_lines('Meta')) == \
            [{'a': 'a1', 'b': 'b1', 'c': 'c1'}]

        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/basic_meta.xlsx', 
                              exclude_sheets=['Meta'])
        xlsxinput.read_sheets()

        assert xlsxinput.sub_sheet_names == ['main', 'subsheet']
        assert list(xlsxinput.get_sheet_lines('main')) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_input_integer(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/integer.xlsx')

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_sheet_lines('main')) == \
            [{'colA': 1}]
        if sys.version_info[0] == 2:
            assert type(list(xlsxinput.get_sheet_lines('main'))[0]['colA']) == long
        else:
            assert type(list(xlsxinput.get_sheet_lines('main'))[0]['colA']) == int
        assert xlsxinput.sub_sheet_names == ['main']

    def test_xlsx_input_integer2(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/integer2.xlsx')

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_sheet_lines('Sheet1')) == \
            [{'activity-status/@code': 2}]
        # This is a float, but is converted to an int in the unflatten step, see
        # test_input_SpreadsheetInput_unflatten.py
        # 'Basic with float'
        assert type(list(xlsxinput.get_sheet_lines('Sheet1'))[0]['activity-status/@code']) == float
        assert xlsxinput.sub_sheet_names == ['Sheet1']

    def test_xlsx_input_formula(self):
        """ When a forumla is present, we should use the value, rather than the
        formula itself. """

        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/formula.xlsx')

        xlsxinput.read_sheets()

        assert xlsxinput.sub_sheet_names == ['main', 'subsheet']
        assert list(xlsxinput.get_sheet_lines('main')) == \
            [{'colA': 1, 'colB': 2}, {'colA': 2, 'colB': 4}]
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 3, 'colD': 9}, {'colC': 4, 'colD': 12}]

    def test_bad_xlsx(self):
        """ XLSX file that is not a XLSX"""

        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/file.xlsx')

        try:
            xlsxinput.read_sheets()
        except Exception as e:
            assert str(e) == "The supplied file has extension .xlsx but isn't an XLSX file."
            return

        assert False, "No Exception Raised"

    def test_ods_input_formula(self):
        """ When a forumla is present, we should use the value, rather than the
        formula itself. """

        odsinput = ODSInput(input_name='flattentool/tests/fixtures/ods/formula.ods')

        odsinput.read_sheets()

        assert list(odsinput.sub_sheet_names) == ['main', 'subsheet']
        assert list(odsinput.get_sheet_lines('main')) == \
            [OrderedDict([('colA', '1'), ('colB', '2')]), OrderedDict([('colA', '2'), ('colB', '4')])]
        assert list(odsinput.get_sheet_lines('subsheet')) == \
            [OrderedDict([('colC', '3'), ('colD', '9')]), OrderedDict([('colC', '4'), ('colD', '12')])]


class TestInputFailure(object):
    def test_csv_no_directory(self):
        csvinput = CSVInput(input_name='nonesensedirectory')
        with pytest.raises(FileNotFoundError):
            csvinput.read_sheets()

    def test_xlsx_no_file(self, tmpdir):
        xlsxinput = XLSXInput(input_name=tmpdir.join('test.xlsx').strpath)
        with pytest.raises(FileNotFoundError):
            xlsxinput.read_sheets()

    def test_ods_no_file(self, tmpdir):
        odsinput = ODSInput(input_name=tmpdir.join('test.ods').strpath)
        if sys.version > '3':
            with pytest.raises(FileNotFoundError):
                odsinput.read_sheets()
        else:
            with pytest.raises(IOError):
                odsinput.read_sheets()


class TestUnicodeInput(object):
    def test_csv_input_utf8(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\néαГ😼𝒞人', encoding='utf8')
        csvinput = CSVInput(input_name=tmpdir.strpath)  # defaults to utf8
        csvinput.read_sheets()
        assert list(csvinput.get_sheet_lines('main')) == \
            [{'colA': 'éαГ😼𝒞人'}]
        assert csvinput.sub_sheet_names == ['main']

    def test_csv_input_latin1(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\né', encoding='latin-1')
        csvinput = CSVInput(input_name=tmpdir.strpath)
        csvinput.encoding = 'latin-1'
        csvinput.read_sheets()
        assert list(csvinput.get_sheet_lines('main')) == \
            [{'colA': 'é'}]
        assert csvinput.sub_sheet_names == ['main']

    @pytest.mark.xfail(
        sys.version_info < (3, 0),
        reason='Python 2 CSV readers does not support UTF-16 (or any encodings with null bytes')
    def test_csv_input_utf16(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\néαГ😼𝒞人', encoding='utf16')
        csvinput = CSVInput(input_name=tmpdir.strpath)
        csvinput.encoding = 'utf16'
        csvinput.read_sheets()
        assert list(csvinput.get_sheet_lines('main')) == \
            [{'colA': 'éαГ😼𝒞人'}]
        assert csvinput.sub_sheet_names == ['main']

    def test_xlsx_input_utf8(self):
        """This is an xlsx file saved by OpenOffice. It seems to use UTF8 internally."""
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/unicode.xlsx')

        xlsxinput.read_sheets()
        assert list(xlsxinput.get_sheet_lines('main'))[0]['id'] == 'éαГ😼𝒞人'


def test_convert_type(recwarn):
    si = SpreadsheetInput()
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
    assert 'Unrecognised value for boolean: "2"' in str(recwarn.pop(UserWarning).message)
    convert_type('boolean', 'test')
    assert 'Unrecognised value for boolean: "test"' in str(recwarn.pop(UserWarning).message)

    convert_type('integer', 'test')
    assert 'Non-integer value "test"' in str(recwarn.pop(UserWarning).message)

    convert_type('number', 'test')
    assert 'Non-numeric value "test"' in str(recwarn.pop(UserWarning).message)

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

    for type_string in ['array', 'string_array', 'array_array', 'number_array']:
        assert convert_type(type_string, 'one') == ['one']
        assert convert_type(type_string, 'one;two') == ['one', 'two']
        assert convert_type(type_string, 'one,two;three,four') == [['one', 'two'], ['three', 'four']]
    assert 'Non-numeric value "one"' in str(recwarn.pop(UserWarning).message)
    assert 'Non-numeric value "one;two"' in str(recwarn.pop(UserWarning).message)
    assert 'Non-numeric value "one,two;three,four"' in str(recwarn.pop(UserWarning).message)
    assert convert_type('number_array', '1') == [1]
    assert convert_type('number_array', '1;2') == [1, 2]
    assert convert_type('number_array', '1,2;3,4') == [[1, 2], [3, 4]]

    with pytest.raises(ValueError) as e:
        convert_type('notatype', 'test')
    assert 'Unrecognised type: "notatype"' in str(e)

    assert convert_type('string', datetime.datetime(2015, 1, 1)) == '2015-01-01T00:00:00+00:00'
    assert convert_type('', datetime.datetime(2015, 1, 1)) == '2015-01-01T00:00:00+00:00'
    assert convert_type('string', datetime.datetime(2015, 1, 1, 13, 37, 59)) == '2015-01-01T13:37:59+00:00'
    assert convert_type('', datetime.datetime(2015, 1, 1, 13, 37, 59)) == '2015-01-01T13:37:59+00:00'

    timezone = pytz.timezone('Europe/London')
    assert convert_type('string', datetime.datetime(2015, 1, 1), timezone) == '2015-01-01T00:00:00+00:00'
    assert convert_type('', datetime.datetime(2015, 1, 1), timezone) == '2015-01-01T00:00:00+00:00'
    assert convert_type('string', datetime.datetime(2015, 1, 1, 13, 37, 59), timezone) == '2015-01-01T13:37:59+00:00'
    assert convert_type('', datetime.datetime(2015, 1, 1, 13, 37, 59), timezone) == '2015-01-01T13:37:59+00:00'
    assert convert_type('string', datetime.datetime(2015, 6, 1), timezone) == '2015-06-01T00:00:00+01:00'
    assert convert_type('', datetime.datetime(2015, 6, 1), timezone) == '2015-06-01T00:00:00+01:00'
    assert convert_type('string', datetime.datetime(2015, 6, 1, 13, 37, 59), timezone) == '2015-06-01T13:37:59+01:00'
    assert convert_type('', datetime.datetime(2015, 6, 1, 13, 37, 59), timezone) == '2015-06-01T13:37:59+01:00'

    assert len(recwarn) == 0
