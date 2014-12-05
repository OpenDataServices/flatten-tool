from flattening_ocds import unflatten, flatten
import json
import pytest


@pytest.mark.parametrize('output_format', ['xlsx', 'csv'])
def test_roundtrip(tmpdir, output_format):
    input_name = 'flattening_ocds/tests/fixtures/tenders_releases_2_releases.json'
    base_name = 'flattening_ocds/tests/fixtures/tenders_releases_base.json'
    flatten(
        input_name=input_name,
        output_name=tmpdir.join('flattened').strpath,
        output_format=output_format,
        schema='flattening_ocds/tests/fixtures/release-schema.json',
        main_sheet_name='release')
    unflatten(
        input_name=tmpdir.join('flattened').strpath,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        base_json=base_name,
        main_sheet_name='release')
    original_json = json.load(open(input_name))
    roundtripped_json = json.load(tmpdir.join('roundtrip.json'))

    # Not currently possible to roundtrib Nones
    # https://github.com/open-contracting/flattening-ocds/issues/35
    for release in roundtripped_json['releases']:
        release['tender']['awardCriteriaDetails'] = None

    assert original_json == roundtripped_json
