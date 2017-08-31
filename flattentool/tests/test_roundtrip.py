from flattentool import unflatten, flatten
import json
import pytest
import sys
import os


@pytest.mark.parametrize('output_format', ['xlsx', 'csv'])
def test_roundtrip(tmpdir, output_format):
    input_name = 'flattentool/tests/fixtures/tenders_releases_2_releases.json'
    base_name = 'flattentool/tests/fixtures/tenders_releases_base.json'
    flatten(
        input_name=input_name,
        output_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_format=output_format,
        schema='flattentool/tests/fixtures/release-schema.json',
        root_list_path='releases',
        main_sheet_name='releases')
    unflatten(
        input_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        base_json=base_name,
        schema='flattentool/tests/fixtures/release-schema.json',
        root_list_path='releases')
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
        root_list_path='grants',
        root_id='',
        use_titles=use_titles,
        main_sheet_name='grants')
    unflatten(
        input_name=tmpdir.join('flattened').strpath+'.'+output_format,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        root_list_path='grants',
        root_id='',
        convert_titles=use_titles)
    original_json = json.load(open(input_name))
    roundtripped_json = json.load(tmpdir.join('roundtrip.json'))

    assert original_json == roundtripped_json


@pytest.mark.parametrize('use_titles', [False, True])
def test_roundtrip_360_rollup(tmpdir, use_titles):
    input_name = 'flattentool/tests/fixtures/WellcomeTrust-grants_fixed_2_grants.json'
    output_format = 'csv'
    output_name = tmpdir.join('flattened').strpath+'.'+output_format
    moved_name = tmpdir.mkdir('flattened_main_only').strpath

    flatten(
        input_name=input_name,
        output_name=output_name,
        output_format=output_format,
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        root_list_path='grants',
        root_id='',
        use_titles=use_titles,
        rollup=True,
        main_sheet_name='grants')

    os.rename(output_name+'/grants.csv', moved_name+'/grants.csv')

    unflatten(
        input_name=moved_name,
        output_name=tmpdir.join('roundtrip.json').strpath,
        input_format=output_format,
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        root_list_path='grants',
        root_id='',
        convert_titles=use_titles)

    original_json = json.load(open(input_name))
    roundtripped_json = json.load(tmpdir.join('roundtrip.json'))
    assert original_json == roundtripped_json
