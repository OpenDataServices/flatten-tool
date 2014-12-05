from flattening_ocds import unflatten, flatten
import json
import pytest

@pytest.mark.xfail
@pytest.mark.parametrize('output_format', ['xlsx', 'csv'])
def test_roundtrip(tmpdir, output_format):
    input_name = 'flattening_ocds/tests/fixtures/tenders_releases_2_releases.json'
    base_name = 'flattening_ocds/tests/fixtures/tenders_releases_base.json'
    flatten(
        input_name=input_name,
        output_name=tmpdir.join('flattened').strpath,
        output_format=output_format,
        main_sheet_name='release')
    unflatten(
        input_name=tmpdir.join('flattened').strpath,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        base_json=base_name,
        main_sheet_name='release')
    assert json.load(open(input_name)) == json.load(tmpdir.join('roundtrip.json'))