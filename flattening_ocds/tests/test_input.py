from flattening_ocds.input import SpreadsheetInput, CSVInput, XLSXInput
from flattening_ocds.input import unflatten_line, unflatten_spreadsheet_input, find_deepest_id_field, convert_type
import pytest


def test_spreadsheetinput_base_fails():
    spreadsheet_input = SpreadsheetInput()
    with pytest.raises(NotImplementedError):
        spreadsheet_input.read_sheets()
    with pytest.raises(NotImplementedError):
        spreadsheet_input.get_sheet_lines('test')


def test_csv_input(tmpdir):
    main = tmpdir.join('main.csv')
    main.write('colA,colB\ncell1,cell2\ncell3,cell4')
    subsheet = tmpdir.join('subsheet.csv')
    subsheet.write('colC,colD\ncell5,cell6\ncell7,cell8')

    csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
    assert csvinput.main_sheet_name == 'main'

    csvinput.read_sheets()

    assert list(csvinput.get_main_sheet_lines()) == \
        [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
    assert csvinput.sub_sheet_names == [ 'subsheet' ]
    assert list(csvinput.get_sheet_lines('subsheet')) == \
        [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]


@pytest.mark.xfail
def test_xlsx_input(tmpdir):
    xlsxinput = XLSXInput(input_name='flattening_ocds/tests/xlsx/basic.xlsx', main_sheet_name='main')
    assert xlsxinput.main_sheet_name == 'main'

    xlsxinput.read_sheets()

    assert list(xlsxinput.get_main_sheet_lines()) == \
        [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
    assert xlsxinput.sub_sheet_names == [ 'subsheet' ]
    assert list(xlsxinput.get_sheet_lines('subsheet')) == \
        [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    


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
                        'custom_main/testA/id:subField': 2,
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
                    {
                        'ocid': 1,
                        'id': 2,
                    }
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
        assert set(unflattened[0]) == set(['sub1Field', 'id', 'ocid'])
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

def test_convert_type():
    assert convert_type('array', 'one;two') == ['one', 'two']
    assert convert_type('array', 'one,two;three,four') == [ ['one', 'two'], ['three', 'four'] ]
