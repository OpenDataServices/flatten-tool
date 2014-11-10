from flattening_ocds  import decimal_default, unflatten
from decimal import Decimal
import json

def test_decimal_default():
    assert json.dumps(Decimal('1.2'), default=decimal_default) == '1.2'
    assert json.dumps(Decimal('42'), default=decimal_default) == '42'


def lines_strip_whitespace(text):
    lines = text.split('\n')
    return '\n'.join(line.strip() for line in lines)


def test_unflatten(tmpdir):
    input_dir = tmpdir.ensure('release_input', dir=True)
    input_dir.join('main.csv').write(
        'ocid,id,testA,testB,testC\n'
        '1,2,3,4,5\n'
        '6,7,8,9,10\n'
    )
    unflatten(input_dir.strpath,
        input_format='csv',
        output_name=tmpdir.join('release').strpath,
        main_sheet_name='main')
    print(tmpdir.join('release.json').read())
    assert lines_strip_whitespace(tmpdir.join('release.json').read()) == lines_strip_whitespace('''{
    "releases": [
        {
            "ocid": "1",
            "id": "2",
            "testA": "3",
            "testB": "4",
            "testC": "5"
        },
        {
            "ocid": "6",
            "id": "7",
            "testA": "8",
            "testB": "9",
            "testC": "10"
        }
    ]
}''')
