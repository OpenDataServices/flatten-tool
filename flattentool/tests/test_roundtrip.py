from flattentool import unflatten, flatten
import json
import pytest
import sys


@pytest.mark.parametrize('output_format', ['xlsx', 'csv'])
def test_roundtrip(tmpdir, output_format):
    input_name = 'flattentool/tests/fixtures/tenders_releases_2_releases.json'
    base_name = 'flattentool/tests/fixtures/tenders_releases_base.json'
    flatten(
        input_name=input_name,
        output_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_format=output_format,
        schema='flattentool/tests/fixtures/release-schema.json',
        main_sheet_name='releases')
    unflatten(
        input_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        base_json=base_name,
        schema='flattentool/tests/fixtures/release-schema.json',
        main_sheet_name='releases')
    original_json = json.load(open(input_name))
    roundtripped_json = json.load(tmpdir.join('roundtrip.json'))

    # Not currently possible to roundtrip Nones
    # https://github.com/open-contracting/flattening-ocds/issues/35
    for release in roundtripped_json['releases']:
        release['tender']['awardCriteriaDetails'] = None

    assert original_json == roundtripped_json


@pytest.mark.parametrize('use_titles', [False, True])
@pytest.mark.parametrize('output_format', ['xlsx', 'csv'])
def test_roundtrip_360(tmpdir, output_format, use_titles):
    input_name = 'flattentool/tests/fixtures/WellcomeTrust-grants_fixed_2_grants.json'
    flatten(
        input_name=input_name,
        output_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_format=output_format,
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        main_sheet_name='grants',
        root_list_path='grants',
        root_id='',
        use_titles=use_titles)
    unflatten(
        input_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        main_sheet_name='grants',
        root_list_path='grants',
        root_id='',
        convert_titles=use_titles)
    original_json = json.load(open(input_name))
    roundtripped_json = json.load(tmpdir.join('roundtrip.json'))

    # Currently not enough information to successfully roundtrip that values
    # are numbers, when this is not required by the schema
    # for CSV, and for openpyxl under Python 2
    if output_format == 'csv' or sys.version_info < (3, 0):
        for grant in original_json['grants']:
            grant['plannedDates'][0]['duration'] = str(grant['plannedDates'][0]['duration'])

    assert original_json == roundtripped_json