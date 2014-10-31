from output import FORMATS


def test_blank_sheets(tmpdir):
    class MockParser(object):
        main_sheet = []
        sub_sheets = {}
    parser = MockParser()
    for spreadsheet_output_class in FORMATS.values():
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name='release')
        spreadsheet_output.write_sheets()
