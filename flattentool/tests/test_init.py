# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flattentool import decimal_default, unflatten
from decimal import Decimal
import json


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
        On an id column haeder, the information following a colon is the key for the array.
        If this is not provided, the sheet name is used.
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
        'ocid,main/id:sub,main/test/id,id,testD,test2/E,test2/F\n'
        '1,2,,S1,11,12,13\n'
        '1,2a,,S1,14,15,16\n'
        '1,2,,S2,17,18,19\n'
        '6,7,,S1,20,21,22\n'
        '1,2,4,S3,24,25,26\n'
    )
    input_dir.join('subsubsheet.csv').write(
        'ocid,main/id,main/sub[]/id:subsub,testG\n'
        '1,2,S1,23\n'
    )
    unflatten(
        input_dir.strpath,
        input_format='csv',
        output_name=tmpdir.join('release.json').strpath,
        main_sheet_name='main')
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
