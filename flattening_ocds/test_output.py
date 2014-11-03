import pytest
from flattening_ocds import output


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
    for spreadsheet_output_class in output.FORMATS.values():
        spreadsheet_output = spreadsheet_output_class(
            parser=MockParser([], {}),
            main_sheet_name='release')
        spreadsheet_output.write_sheets()
    # TODO Actually check the sheets are blank


def test_populated_sheets(tmpdir):
    for spreadsheet_output_class in output.FORMATS.values():
        spreadsheet_output = spreadsheet_output_class(
            parser=MockParser(['a'], {'b': 'c'}),
            main_sheet_name='release')
        spreadsheet_output.write_sheets()
    # TODO Actually check the sheets are populated
