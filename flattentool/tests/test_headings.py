from collections import OrderedDict
from flattentool.input import SpreadsheetInput, WITH_CELLS
from flattentool.schema import SchemaParser
from jsonref import JsonRef
import pytest


test_heading_warning_data = [
    (
        ['a', 'a'],
        [
            # Check we use the later values
            [1, 2],
        ],
        [
            'Duplicate heading "a" found, ignoring the data in column A.'
        ],
        ([OrderedDict([('a', 2)])], None, None),
    ),
    (
        ['a', 'b', 'c', 'b', 'c', 'c', 'd', 'd', 'd', 'd'],
        [
            # Check for warnings even with empty cells
            [1,],
        ],
        [
            'Duplicate heading "b" found, ignoring the data in column B.',
            'Duplicate heading "c" found, ignoring the data in columns C and E.',
            'Duplicate heading "d" found, ignoring the data in columns G, H and I.',
        ],
        ([OrderedDict([('a', 1)])], None, None),
    ),
]


@pytest.mark.parametrize(
    'headings, rows, expected_warnings, expected_result',
    test_heading_warning_data
)
def test_duplicate_headings_give_warning(headings, rows, expected_warnings, expected_result):
    sheets = [
        {
            'name': 'main',
            'headings': headings,
            'rows': rows,
        }
    ]
    with pytest.warns(UserWarning) as type_warnings:
        result = run(sheets)
    # Check that only one warning was raised
    assert len(type_warnings) == len(expected_warnings)
    # Check that the message matches
    messages = [type_warning.message.args[0] for type_warning in type_warnings]
    assert messages == expected_warnings
    assert result == expected_result


class HeadingListInput(SpreadsheetInput):
    def __init__(self, sheets, headings, **kwargs):
        self.sheets = sheets
        self.headings = headings
        super(HeadingListInput, self).__init__(**kwargs)

    def get_sheet_lines(self, sheet_name):
        return self.sheets[sheet_name]

    def get_sheet_headings(self, sheet_name):
        return self.headings[sheet_name]

    def read_sheets(self):
        self.sub_sheet_names = list(self.sheets.keys())


def run(sheets, schema=None, source_maps=False):
    if not WITH_CELLS:
        source_maps = False
    input_headings = OrderedDict()
    input_sheets = OrderedDict()
    for sheet in sheets:
        rows = []
        for row in sheet['rows']:
            rows.append(OrderedDict(zip(sheet['headings'], row)))
        input_sheets[sheet['name']] = rows
        input_headings[sheet['name']] = sheet['headings']
    if schema is not None:
        spreadsheet_input = HeadingListInput(
            input_sheets,
            input_headings,
            root_id='',
            # Without this, titles from a schema aren't understood
            convert_titles=True,
        )
        # Without this, the $ref entries in the schema aren't resolved.
        dereferenced_schema = JsonRef.replace_refs(schema)
        parser = SchemaParser(
            root_schema_dict=dereferenced_schema,
            root_id='main',
            rollup=True
        )
        parser.parse()
        spreadsheet_input.parser = parser
    else:
        spreadsheet_input = HeadingListInput(
            input_sheets,
            input_headings,
            root_id='',
        )
    spreadsheet_input.read_sheets()
    if source_maps:
        result, cell_source_map_data, heading_source_map_data = spreadsheet_input.fancy_unflatten()
        return result, cell_source_map_data, heading_source_map_data
    else:
        return spreadsheet_input.unflatten(), None, None
