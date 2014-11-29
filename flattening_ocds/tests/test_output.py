import pytest
import os
from flattening_ocds import output, schema
import openpyxl


class MockParser(object):
    def __init__(self, main_sheet, sub_sheets):
        self.main_sheet = main_sheet
        self.sub_sheets = sub_sheets


def test_spreadsheetouput_base_fails():
    """The base class should fail as it is missing functionality that child
    classes must implement"""

    spreadsheet_output = output.SpreadsheetOutput(parser=MockParser([], {}))
    with pytest.raises(NotImplementedError):
        spreadsheet_output.write_sheets()


def test_blank_sheets(tmpdir):
    for format_name, spreadsheet_output_class in output.FORMATS.items():
        spreadsheet_output = spreadsheet_output_class(
            parser=MockParser([], {}),
            main_sheet_name='release',
            output_name=os.path.join(tmpdir.strpath, 'release'+output.FORMATS_SUFFIX[format_name]))
        spreadsheet_output.write_sheets()

    # Check XLSX is empty
    wb = openpyxl.load_workbook(tmpdir.join('release.xlsx').strpath)
    assert wb.get_sheet_names() == ['release']
    assert len(wb['release'].rows) == 1
    assert len(wb['release'].rows[0]) == 1
    assert wb['release'].rows[0][0].value == None
    
    # Check CSV is Empty
    assert tmpdir.join('release').listdir() == [ tmpdir.join('release').join('release.csv') ]
    assert tmpdir.join('release', 'release.csv').read().strip('\n') == ''


def test_populated_sheets(tmpdir):
    for format_name, spreadsheet_output_class in output.FORMATS.items():
        subsheet = schema.SubSheet()
        subsheet.add_field('c')
        spreadsheet_output = spreadsheet_output_class(
            parser=MockParser(['a'], {'b': subsheet}),
            main_sheet_name='release',
            output_name=os.path.join(tmpdir.strpath, 'release'+output.FORMATS_SUFFIX[format_name]))
        spreadsheet_output.write_sheets()

    # Check XLSX
    wb = openpyxl.load_workbook(tmpdir.join('release.xlsx').strpath)
    assert wb.get_sheet_names() == ['release', 'b']
    assert len(wb['release'].rows) == 1
    assert [ x.value for x in wb['release'].rows[0] ] == [ 'a' ]
    assert len(wb['b'].rows) == 1
    assert [ x.value for x in wb['b'].rows[0] ] == [ 'ocid', 'c' ]

    # Check CSV
    assert set(tmpdir.join('release').listdir()) == set([
        tmpdir.join('release').join('release.csv'),
        tmpdir.join('release').join('b.csv')
    ])
    assert tmpdir.join('release', 'release.csv').read().strip('\n') == 'a'
    assert tmpdir.join('release', 'b.csv').read().strip('\n') == 'ocid,c'
