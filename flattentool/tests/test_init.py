# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flattentool import decimal_default, unflatten
from decimal import Decimal
import json
import sys
import pytest


def original_cell_and_row_locations(data):
    '''
    Cells should each appear only once

    Rows should appear the number of times a column in it resolves to a unique dictionary
    '''
    cells = []
    rows = {}
    for key in data:
        cell_list = data[key]
        for cell in cell_list:
            if len(cell) == 2:
                # This is a row
                row_str = '{}:{}'.format(cell[0], cell[1])
                if row_str not in rows:
                    rows[row_str] = 1
                else:
                    rows[row_str] += 1
            else:
                # This is a cell
                cell_str = '{}:{}{}'.format(cell[0], cell[1], cell[2])
                assert cell_str not in cells
                cells.append(cell_str)
    cells.sort()
    return cells, rows


def original_headings(heading_data):
    '''\
    '''
    headings = []
    for key in heading_data:
        cell_list = heading_data[key]
        for cell in cell_list:
            assert len(cell) == 2
            heading_str = '{}:{}'.format(cell[0], cell[1])
            assert heading_str not in headings
            headings.append(heading_str)
    headings.sort()
    return headings


def test_decimal_default():
    assert json.dumps(Decimal('1.2'), default=decimal_default) == '1.2'
    assert json.dumps(Decimal('42'), default=decimal_default) == '42'


def lines_strip_whitespace(text):
    lines = text.split('\n')
    return '\n'.join(line.strip() for line in lines)


def test_unflatten(tmpdir):
    """
    Perform a full CSV unflattening, and check the output is what we expect.

    Notable things we are checking for:
        Ordering is preseved - both the order of columns and rows
    """
    input_dir = tmpdir.ensure('release_input', dir=True)
    input_dir.join('main.csv').write(
        'ocid,id,testA,test/id,test/C\n'
        '1,2,3,4,5\n'
        '1,2a,3a,4a,5a\n'
        '6,7,8,9,10\n'
        '6,7a,8a,9a,10a\n'
    )
    input_dir.join('subsheet.csv').write(
        'ocid,id,sub/0/id,sub/0/testD,sub/0/test2/E,sub/0/test2/F\n'
        '1,2,S1,11,12,13\n'
        '1,2a,S1,14,15,16\n'
        '1,2,S2,17,18,19\n'
        '6,7,S1,20,21,22\n'
    )
    input_dir.join('subsheet_test.csv').write(
        'ocid,id,test/id,test/subsheet/0/id,test/subsheet/0/testD,test/subsheet/0/test2/E,test/subsheet/0/test2/F\n'
        '1,2,4,S3,24,25,26\n'
    )
    input_dir.join('subsubsheet.csv').write(
        'ocid,id,sub/0/id,sub/0/subsub/0/testG\n'
        '1,2,S1,23\n'
    )
    unflatten(
        input_dir.strpath,
        input_format='csv',
        output_name=tmpdir.join('release.json').strpath,
        main_sheet_name='main',
        cell_source_map=tmpdir.join('cell_source_map.json').strpath,
        heading_source_map=tmpdir.join('heading_source_map.json').strpath)
    # Note, "main/0/testA": comes after "main/0/test" because 'testA' > 'testA'
    # Note also that all the row entries come after the cell ones
    expected = '''{
        "main/0/id": [
            [
                "main",
                "B",
                2,
                "id"
            ],
            [
                "subsheet",
                "B",
                2,
                "id"
            ],
            [
                "subsheet",
                "B",
                4,
                "id"
            ],
            [
                "subsheet_test",
                "B",
                2,
                "id"
            ],
            [
                "subsubsheet",
                "B",
                2,
                "id"
            ]
        ],
        "main/0/ocid": [
            [
                "main",
                "A",
                2,
                "ocid"
            ],
            [
                "subsheet",
                "A",
                2,
                "ocid"
            ],
            [
                "subsheet",
                "A",
                4,
                "ocid"
            ],
            [
                "subsheet_test",
                "A",
                2,
                "ocid"
            ],
            [
                "subsubsheet",
                "A",
                2,
                "ocid"
            ]
        ],
        "main/0/sub/0/id": [
            [
                "subsheet",
                "C",
                2,
                "sub/0/id"
            ],
            [
                "subsubsheet",
                "C",
                2,
                "sub/0/id"
            ]
        ],
        "main/0/sub/0/subsub/0/testG": [
            [
                "subsubsheet",
                "D",
                2,
                "sub/0/subsub/0/testG"
            ]
        ],
        "main/0/sub/0/test2/E": [
            [
                "subsheet",
                "E",
                2,
                "sub/0/test2/E"
            ]
        ],
        "main/0/sub/0/test2/F": [
            [
                "subsheet",
                "F",
                2,
                "sub/0/test2/F"
            ]
        ],
        "main/0/sub/0/testD": [
            [
                "subsheet",
                "D",
                2,
                "sub/0/testD"
            ]
        ],
        "main/0/sub/1/id": [
            [
                "subsheet",
                "C",
                4,
                "sub/0/id"
            ]
        ],
        "main/0/sub/1/test2/E": [
            [
                "subsheet",
                "E",
                4,
                "sub/0/test2/E"
            ]
        ],
        "main/0/sub/1/test2/F": [
            [
                "subsheet",
                "F",
                4,
                "sub/0/test2/F"
            ]
        ],
        "main/0/sub/1/testD": [
            [
                "subsheet",
                "D",
                4,
                "sub/0/testD"
            ]
        ],
        "main/0/test/C": [
            [
                "main",
                "E",
                2,
                "test/C"
            ]
        ],
        "main/0/test/id": [
            [
                "main",
                "D",
                2,
                "test/id"
            ],
            [
                "subsheet_test",
                "C",
                2,
                "test/id"
            ]
        ],
        "main/0/test/subsheet/0/id": [
            [
                "subsheet_test",
                "D",
                2,
                "test/subsheet/0/id"
            ]
        ],
        "main/0/test/subsheet/0/test2/E": [
            [
                "subsheet_test",
                "F",
                2,
                "test/subsheet/0/test2/E"
            ]
        ],
        "main/0/test/subsheet/0/test2/F": [
            [
                "subsheet_test",
                "G",
                2,
                "test/subsheet/0/test2/F"
            ]
        ],
        "main/0/test/subsheet/0/testD": [
            [
                "subsheet_test",
                "E",
                2,
                "test/subsheet/0/testD"
            ]
        ],
        "main/0/testA": [
            [
                "main",
                "C",
                2,
                "testA"
            ]
        ],
        "main/1/id": [
            [
                "main",
                "B",
                3,
                "id"
            ],
            [
                "subsheet",
                "B",
                3,
                "id"
            ]
        ],
        "main/1/ocid": [
            [
                "main",
                "A",
                3,
                "ocid"
            ],
            [
                "subsheet",
                "A",
                3,
                "ocid"
            ]
        ],
        "main/1/sub/0/id": [
            [
                "subsheet",
                "C",
                3,
                "sub/0/id"
            ]
        ],
        "main/1/sub/0/test2/E": [
            [
                "subsheet",
                "E",
                3,
                "sub/0/test2/E"
            ]
        ],
        "main/1/sub/0/test2/F": [
            [
                "subsheet",
                "F",
                3,
                "sub/0/test2/F"
            ]
        ],
        "main/1/sub/0/testD": [
            [
                "subsheet",
                "D",
                3,
                "sub/0/testD"
            ]
        ],
        "main/1/test/C": [
            [
                "main",
                "E",
                3,
                "test/C"
            ]
        ],
        "main/1/test/id": [
            [
                "main",
                "D",
                3,
                "test/id"
            ]
        ],
        "main/1/testA": [
            [
                "main",
                "C",
                3,
                "testA"
            ]
        ],
        "main/2/id": [
            [
                "main",
                "B",
                4,
                "id"
            ],
            [
                "subsheet",
                "B",
                5,
                "id"
            ]
        ],
        "main/2/ocid": [
            [
                "main",
                "A",
                4,
                "ocid"
            ],
            [
                "subsheet",
                "A",
                5,
                "ocid"
            ]
        ],
        "main/2/sub/0/id": [
            [
                "subsheet",
                "C",
                5,
                "sub/0/id"
            ]
        ],
        "main/2/sub/0/test2/E": [
            [
                "subsheet",
                "E",
                5,
                "sub/0/test2/E"
            ]
        ],
        "main/2/sub/0/test2/F": [
            [
                "subsheet",
                "F",
                5,
                "sub/0/test2/F"
            ]
        ],
        "main/2/sub/0/testD": [
            [
                "subsheet",
                "D",
                5,
                "sub/0/testD"
            ]
        ],
        "main/2/test/C": [
            [
                "main",
                "E",
                4,
                "test/C"
            ]
        ],
        "main/2/test/id": [
            [
                "main",
                "D",
                4,
                "test/id"
            ]
        ],
        "main/2/testA": [
            [
                "main",
                "C",
                4,
                "testA"
            ]
        ],
        "main/3/id": [
            [
                "main",
                "B",
                5,
                "id"
            ]
        ],
        "main/3/ocid": [
            [
                "main",
                "A",
                5,
                "ocid"
            ]
        ],
        "main/3/test/C": [
            [
                "main",
                "E",
                5,
                "test/C"
            ]
        ],
        "main/3/test/id": [
            [
                "main",
                "D",
                5,
                "test/id"
            ]
        ],
        "main/3/testA": [
            [
                "main",
                "C",
                5,
                "testA"
            ]
        ],
        "main/0": [
            [
                "main",
                2
            ],
            [
                "subsheet",
                2
            ],
            [
                "subsheet",
                4
            ],
            [
                "subsheet_test",
                2
            ],
            [
                "subsubsheet",
                2
            ]
        ],
        "main/0/sub/0": [
            [
                "subsheet",
                2
            ],
            [
                "subsubsheet",
                2
            ]
        ],
        "main/0/sub/0/subsub/0": [
            [
                "subsubsheet",
                2
            ]
        ],
        "main/0/sub/0/test2": [
            [
                "subsheet",
                2
            ]
        ],
        "main/0/sub/1": [
            [
                "subsheet",
                4
            ]
        ],
        "main/0/sub/1/test2": [
            [
                "subsheet",
                4
            ]
        ],
        "main/0/test": [
            [
                "main",
                2
            ],
            [
                "subsheet_test",
                2
            ]
        ],
        "main/0/test/subsheet/0": [
            [
                "subsheet_test",
                2
            ]
        ],
        "main/0/test/subsheet/0/test2": [
            [
                "subsheet_test",
                2
            ]
        ],
        "main/1": [
            [
                "main",
                3
            ],
            [
                "subsheet",
                3
            ]
        ],
        "main/1/sub/0": [
            [
                "subsheet",
                3
            ]
        ],
        "main/1/sub/0/test2": [
            [
                "subsheet",
                3
            ]
        ],
        "main/1/test": [
            [
                "main",
                3
            ]
        ],
        "main/2": [
            [
                "main",
                4
            ],
            [
                "subsheet",
                5
            ]
        ],
        "main/2/sub/0": [
            [
                "subsheet",
                5
            ]
        ],
        "main/2/sub/0/test2": [
            [
                "subsheet",
                5
            ]
        ],
        "main/2/test": [
            [
                "main",
                4
            ]
        ],
        "main/3": [
            [
                "main",
                5
            ]
        ],
        "main/3/test": [
            [
                "main",
                5
            ]
        ]
    }'''
    assert lines_strip_whitespace(tmpdir.join('cell_source_map.json').read()) == lines_strip_whitespace(expected)
    data = json.loads(expected)
    cells, rows = original_cell_and_row_locations(data) 
    # Make sure every cell in the original appeared in the cell source map exactly once
    assert cells == [
        'main:A2',
        'main:A3',
        'main:A4',
        'main:A5',
        'main:B2',
        'main:B3',
        'main:B4',
        'main:B5',
        'main:C2',
        'main:C3',
        'main:C4',
        'main:C5',
        'main:D2',
        'main:D3',
        'main:D4',
        'main:D5',
        'main:E2',
        'main:E3',
        'main:E4',
        'main:E5',
        'subsheet:A2',
        'subsheet:A3',
        'subsheet:A4',
        'subsheet:A5',
        'subsheet:B2',
        'subsheet:B3',
        'subsheet:B4',
        'subsheet:B5',
        'subsheet:C2',
        'subsheet:C3',
        'subsheet:C4',
        'subsheet:C5',
        'subsheet:D2',
        'subsheet:D3',
        'subsheet:D4',
        'subsheet:D5',
        'subsheet:E2',
        'subsheet:E3',
        'subsheet:E4',
        'subsheet:E5',
        'subsheet:F2',
        'subsheet:F3',
        'subsheet:F4',
        'subsheet:F5',
        'subsheet_test:A2',
        'subsheet_test:B2',
        'subsheet_test:C2',
        'subsheet_test:D2',
        'subsheet_test:E2',
        'subsheet_test:F2',
        'subsheet_test:G2',
        'subsubsheet:A2',
        'subsubsheet:B2',
        'subsubsheet:C2',
        'subsubsheet:D2'
    ]
    # Make sure every row in the original appeared the number of times a column in it resolves to a unique dictionary
    assert rows == {
        'main:2': 2,
        'main:3': 2,
        'main:4': 2,
        'main:5': 2,
        'subsheet:2': 3,
        'subsheet:3': 3,
        'subsheet:4': 3,
        'subsheet:5': 3,
        'subsheet_test:2': 4,
        'subsubsheet:2': 3,
    }
    # TODO Check column names with a JSON schema
    expected_headings = '''{
        "main/id": [
            [
                "main",
                "id"
            ],
            [
                "subsheet",
                "id"
            ],
            [
                "subsheet_test",
                "id"
            ],
            [
                "subsubsheet",
                "id"
            ]
        ],
        "main/ocid": [
            [
                "main",
                "ocid"
            ],
            [
                "subsheet",
                "ocid"
            ],
            [
                "subsheet_test",
                "ocid"
            ],
            [
                "subsubsheet",
                "ocid"
            ]
        ],
        "main/sub/id": [
            [
                "subsheet",
                "sub/0/id"
            ],
            [
                "subsubsheet",
                "sub/0/id"
            ]
        ],
        "main/sub/subsub/testG": [
            [
                "subsubsheet",
                "sub/0/subsub/0/testG"
            ]
        ],
        "main/sub/test2/E": [
            [
                "subsheet",
                "sub/0/test2/E"
            ]
        ],
        "main/sub/test2/F": [
            [
                "subsheet",
                "sub/0/test2/F"
            ]
        ],
        "main/sub/testD": [
            [
                "subsheet",
                "sub/0/testD"
            ]
        ],
        "main/test/C": [
            [
                "main",
                "test/C"
            ]
        ],
        "main/test/id": [
            [
                "main",
                "test/id"
            ],
            [
                "subsheet_test",
                "test/id"
            ]
        ],
        "main/test/subsheet/id": [
            [
                "subsheet_test",
                "test/subsheet/0/id"
            ]
        ],
        "main/test/subsheet/test2/E": [
            [
                "subsheet_test",
                "test/subsheet/0/test2/E"
            ]
        ],
        "main/test/subsheet/test2/F": [
            [
                "subsheet_test",
                "test/subsheet/0/test2/F"
            ]
        ],
        "main/test/subsheet/testD": [
            [
                "subsheet_test",
                "test/subsheet/0/testD"
            ]
        ],
        "main/testA": [
            [
                "main",
                "testA"
            ]
        ]
    }'''
    assert lines_strip_whitespace(tmpdir.join('heading_source_map.json').read()) == lines_strip_whitespace(expected_headings)
    heading_data = json.loads(expected_headings)
    headings = original_headings(heading_data)
    # Make sure every heading in the original appeared in the heading source map exactly once
    assert headings == [
        'main:id',
        'main:ocid',
        'main:test/C',
        'main:test/id',
        'main:testA',

        'subsheet:id',
        'subsheet:ocid',
        'subsheet:sub/0/id',
        'subsheet:sub/0/test2/E',
        'subsheet:sub/0/test2/F',
        'subsheet:sub/0/testD',

        'subsheet_test:id',
        'subsheet_test:ocid',
        'subsheet_test:test/id',
        'subsheet_test:test/subsheet/0/id',
        'subsheet_test:test/subsheet/0/test2/E',
        'subsheet_test:test/subsheet/0/test2/F',
        'subsheet_test:test/subsheet/0/testD',

        'subsubsheet:id',
        'subsubsheet:ocid',
        'subsubsheet:sub/0/id',
        'subsubsheet:sub/0/subsub/0/testG',
    ]
    assert lines_strip_whitespace(tmpdir.join('release.json').read()) == lines_strip_whitespace('''{
    "main": [
        {
            "ocid": "1",
            "id": "2",
            "testA": "3",
            "test": {
                "id": "4",
                "C": "5",
                "subsheet": [
                    {
                        "id": "S3",
                        "testD": "24",
                        "test2": {
                            "E": "25",
                            "F": "26"
                        }
                    }
                ]
            },
            "sub": [
                {
                    "id": "S1",
                    "testD": "11",
                    "test2": {
                        "E": "12",
                        "F": "13"
                    },
                    "subsub": [
                        {
                            "testG": "23"
                        }
                    ]
                },
                {
                    "id": "S2",
                    "testD": "17",
                    "test2": {
                        "E": "18",
                        "F": "19"
                    }
                }
            ]
        },
        {
            "ocid": "1",
            "id": "2a",
            "testA": "3a",
            "test": {
                "id": "4a",
                "C": "5a"
            },
            "sub": [
                {
                    "id": "S1",
                    "testD": "14",
                    "test2": {
                        "E": "15",
                        "F": "16"
                    }
                }
            ]
        },
        {
            "ocid": "6",
            "id": "7",
            "testA": "8",
            "test": {
                "id": "9",
                "C": "10"
            },
            "sub": [
                {
                    "id": "S1",
                    "testD": "20",
                    "test2": {
                        "E": "21",
                        "F": "22"
                    }
                }
            ]
        },
        {
            "ocid": "6",
            "id": "7a",
            "testA": "8a",
            "test": {
                "id": "9a",
                "C": "10a"
            }
        }
    ]
}''')


def test_unflatten_empty(tmpdir):
    input_dir = tmpdir.ensure('release_input', dir=True)
    input_dir.join('main.csv').write_text(
        'ocid,id\n,\n,\n,',
        encoding='utf8'
    )
    unflatten(
        input_dir.strpath,
        input_format='csv',
        output_name=tmpdir.join('release.json').strpath,
        main_sheet_name='main')
    assert lines_strip_whitespace(tmpdir.join('release.json').read()) == lines_strip_whitespace('''{
        "main": []
    }''')


def test_unflatten_csv_utf8(tmpdir):
    input_dir = tmpdir.ensure('release_input', dir=True)
    input_dir.join('main.csv').write_text(
        'ocid,id\n1,éαГ😼𝒞人\n',
        encoding='utf8'
    )
    unflatten(
        input_dir.strpath,
        input_format='csv',
        # Should default to utf8
        output_name=tmpdir.join('release.json').strpath,
        main_sheet_name='main')
    reloaded_json = json.load(tmpdir.join('release.json'))
    assert reloaded_json == {'main': [{'ocid': '1', 'id': 'éαГ😼𝒞人'}]}
    # The JSON we output should be UTF-8, rather than escaped ASCII
    # https://github.com/OpenDataServices/flatten-tool/issues/71
    assert 'éαГ😼𝒞人' in tmpdir.join('release.json').read_text(encoding='utf-8')


def test_unflatten_csv_latin1(tmpdir):
    input_dir = tmpdir.ensure('release_input', dir=True)
    input_dir.join('main.csv').write_text(
        'ocid,id\n1,é\n',
        encoding='latin1'
    )
    unflatten(
        input_dir.strpath,
        input_format='csv',
        encoding='latin1',
        output_name=tmpdir.join('release.json').strpath,
        main_sheet_name='main')
    reloaded_json = json.load(tmpdir.join('release.json'))
    assert reloaded_json == {'main': [{'ocid': '1', 'id': 'é'}]}


def test_unflatten_xslx_unicode(tmpdir):
    unflatten(
        'flattentool/tests/fixtures/xlsx/unicode.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('release.json').strpath,
        main_sheet_name='main')
    reloaded_json = json.load(tmpdir.join('release.json'))
    assert reloaded_json == {'main': [{'ocid': 1, 'id': 'éαГ😼𝒞人'}]}

def test_metatab(tmpdir):
    tmpdir.join('metatab_schema.json').write(
        '{"properties": {}}' 
    )

    unflatten(
        'flattentool/tests/fixtures/xlsx/basic_meta.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('meta_unflattened.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True,
        metatab_schema = tmpdir.join('metatab_schema.json').strpath,
        cell_source_map=tmpdir.join('meta_cell_source_map.json').strpath,
        heading_source_map=tmpdir.join('meta_heading_source_map.json').strpath,
        )

    metatab_json = json.load(tmpdir.join('meta_unflattened.json'))

    assert metatab_json == {'a': 'a1',
                             'b': 'b1',
                             'c': 'c1',
                             'main': [{'colA': 'cell1', 'colB': 'cell2'},
                                      {'colA': 'cell3', 'colB': 'cell4'},
                                      {'colC': 'cell5', 'colD': 'cell6'},
                                      {'colC': 'cell7', 'colD': 'cell8'}]}


    cell_source_map = json.load(tmpdir.join('meta_cell_source_map.json'))

    assert cell_source_map ==  {'': [['Meta', 2]],
                                'a': [['Meta', '1', 2, 'a']],
                                'b': [['Meta', '2', 2, 'b']],
                                'c': [['Meta', '3', 2, 'c']],
                                'main/0': [['main', 2]],
                                'main/0/colA': [['main', 'A', 2, 'colA']],
                                'main/0/colB': [['main', 'B', 2, 'colB']],
                                'main/1': [['main', 3]],
                                'main/1/colA': [['main', 'A', 3, 'colA']],
                                'main/1/colB': [['main', 'B', 3, 'colB']],
                                'main/2': [['subsheet', 2]],
                                'main/2/colC': [['subsheet', 'A', 2, 'colC']],
                                'main/2/colD': [['subsheet', 'B', 2, 'colD']],
                                'main/3': [['subsheet', 3]],
                                'main/3/colC': [['subsheet', 'A', 3, 'colC']],
                                'main/3/colD': [['subsheet', 'B', 3, 'colD']]}

    heading_source_map = json.load(tmpdir.join('meta_heading_source_map.json'))

    assert heading_source_map == {'a': [['Meta', 'a']],
                                  'b': [['Meta', 'b']],
                                  'c': [['Meta', 'c']],
                                  'main/colA': [['main', 'colA']],
                                  'main/colB': [['main', 'colB']],
                                  'main/colC': [['subsheet', 'colC']],
                                  'main/colD': [['subsheet', 'colD']]}

def test_metatab_only(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/basic_meta.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('meta_unflattened.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True,
        metatab_only=True,
        cell_source_map=tmpdir.join('meta_cell_source_map.json').strpath,
        heading_source_map=tmpdir.join('meta_heading_source_map.json').strpath,
        )

    metatab_json = json.load(tmpdir.join('meta_unflattened.json'))

    assert metatab_json == {'a': 'a1',
                            'b': 'b1',
                            'c': 'c1'}


    cell_source_map = json.load(tmpdir.join('meta_cell_source_map.json'))

    assert cell_source_map ==  {'': [['Meta', 2]],
                                'a': [['Meta', '1', 2, 'a']],
                                'b': [['Meta', '2', 2, 'b']],
                                'c': [['Meta', '3', 2, 'c']]}

    heading_source_map = json.load(tmpdir.join('meta_heading_source_map.json'))

    assert heading_source_map == {'a': [['Meta', 'a']],
                                  'b': [['Meta', 'b']],
                                  'c': [['Meta', 'c']]}

def test_metatab_with_base(tmpdir):
    tmpdir.join('base_json.json').write(
        '{}' 
    )

    with pytest.raises(Exception):
        unflatten(
            'flattentool/tests/fixtures/xlsx/basic_meta.xlsx',
            input_format='xlsx',
            output_name=tmpdir.join('meta_unflattened.json').strpath,
            metatab_name='Meta',
            metatab_vertical_orientation=True,
            base_json = tmpdir.join('base_json.json').strpath,
            )

def test_bad_format(tmpdir):
    with pytest.raises(Exception):
        unflatten(
            'flattentool/tests/fixtures/xlsx/basic_meta.xlsx',
            input_format='what',
            output_name=tmpdir.join('meta_unflattened.json').strpath,
            )

    with pytest.raises(Exception):
        unflatten(
            'flattentool/tests/fixtures/xlsx/basic_meta.xlsx',
            input_format=None,
            output_name=tmpdir.join('meta_unflattened.json').strpath,
            )

def test_commands_single_sheet_xlsx(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_in_file.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('command_single_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_single_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_single_heading_source_map.json').strpath,
        )

    unflattened = json.load(tmpdir.join('command_single_unflattened.json'))

    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}]}

def test_commands_single_sheet_csv(tmpdir):
    unflatten(
        'flattentool/tests/fixtures/csv/commands_in_file',
        input_format='csv',
        output_name=tmpdir.join('command_single_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_single_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_single_heading_source_map.json').strpath,
        )
    unflattened = json.load(tmpdir.join('command_single_unflattened.json'))
    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}]}

def test_commands_metatab(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_in_metatab.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('command_metatab_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_metatab_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_metatab_heading_source_map.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True
        )

    unflattened = json.load(tmpdir.join('command_metatab_unflattened.json'))

    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}, {'actual': 'actual', 'headings': 'Other data', 'some': 'some'}],
                           'some': 'data'}

def test_commands_single_sheet_default(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_defaulted.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('command_single_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_single_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_single_heading_source_map.json').strpath,
        default_configuration="SkipRows 1, headerrows 2",
        )

    unflattened = json.load(tmpdir.join('command_single_unflattened.json'))

    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}]}


    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_defaulted.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('command_single_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_single_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_single_heading_source_map.json').strpath,
        default_configuration="SkipRows 1",
        )

    unflattened = json.load(tmpdir.join('command_single_unflattened.json'))

    assert unflattened == {'main': [{'actual': 'other', 'headings': 'headings', 'some': 'some'}, {'actual': 'actual', 'headings': 'data', 'some': 'some'}]}


def test_commands_default_override(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_in_metatab_defaulted.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('command_metatab_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_metatab_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_metatab_heading_source_map.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True,
        default_configuration="headerrows 2",
        )

    unflattened = json.load(tmpdir.join('command_metatab_unflattened.json'))

    # In this case want both 'headerrows 2' and 'skiprows 1' (which is defined in the metatab) to be used,
    # as we only override individual commands not all of them,
    # So the results in this case will be the same as if using commands_in_metatab.xlsx (where all commands are in metatab).

    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}, {'actual': 'actual', 'headings': 'Other data', 'some': 'some'}],
                           'some': 'data'}


def test_commands_ignore(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_ignore.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('command_single_unflattened.json').strpath,
        cell_source_map=tmpdir.join('command_single_source_map.json').strpath,
        heading_source_map=tmpdir.join('command_single_heading_source_map.json').strpath,
        )

    unflattened = json.load(tmpdir.join('command_single_unflattened.json'))

    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}]}

def test_commands_hashcomments(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_hashcomments.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('commands_hashcomments_unflattened.json').strpath,
        cell_source_map=tmpdir.join('commands_hashcomments_source_map.json').strpath,
        heading_source_map=tmpdir.join('commands_hashcomments_heading_source_map.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True
        )

    unflattened = json.load(tmpdir.join('commands_hashcomments_unflattened.json'))

    assert unflattened == {'main': [{'actual': 'actual', 'headings': 'data', 'some': 'some'}, {'actual': 'actual', 'headings': 'Other data', 'some': 'some'}],
                           'some': 'data'}


def test_commands_hashcomments_sourcemap(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_hashcomments_sourcemap.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('commands_hashcomments_unflattened.json').strpath,
        cell_source_map=tmpdir.join('commands_hashcomments_source_map.json').strpath,
        heading_source_map=tmpdir.join('commands_hashcomments_heading_source_map.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True
        )

    unflattened = json.load(tmpdir.join('commands_hashcomments_unflattened.json'))
    cell_source_map = json.load(tmpdir.join('commands_hashcomments_source_map.json'))

    assert unflattened == {'publishedDate': '2019-06-20T00:00:00Z',
                           'publisher': {
                               'name': 'Open Data Services Co-operative'
                           },
                           'uri': 'http://www.example.com',
                           'version': '1.1',
                           'main': [{'date': '2010-03-15T09:30:00Z', 'id': 'Ocds-1'}]
                          }

    # check fields have correct column letters
    assert cell_source_map['main/0/date'][0][1] == 'E'
    assert cell_source_map['main/0/id'][0][1] == 'C'


def test_commands_id_name(tmpdir):

    unflatten(
        'flattentool/tests/fixtures/xlsx/commands_id_name.xlsx',
        input_format='xlsx',
        output_name=tmpdir.join('commands_id_name_unflattened.json').strpath,
        cell_source_map=tmpdir.join('commands_id_name_source_map.json').strpath,
        heading_source_map=tmpdir.join('commands_id_name_heading_source_map.json').strpath,
        metatab_name='Meta',
        metatab_vertical_orientation=True
        )

    unflattened = json.load(tmpdir.join('commands_id_name_unflattened.json'))

    assert unflattened == {'someroot': [{'actual': 'actual', 'headings': 'data', 'someId': 'some',
                                "someArray": [
                                    {"heading1": "more data", "heading2": "other data"},
                                    {"heading1": "more more data", "heading2": "more other data"},
                                ]
                            }],
                           'some': 'data'}
