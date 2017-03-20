import json

from flattentool import unflatten

def test_360_main_sheetname_insensitive(tmpdir):
    input_name = 'flattentool/tests/fixtures/xlsx/WellcomeTrust-grants_2_grants.xlsx'
    unflatten(
        input_name=input_name,
        output_name=tmpdir.join('output_grant.json').strpath,
        input_format='xlsx',
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        main_sheet_name='grants',
        root_list_path='grants',
        root_id='',
        convert_titles=True)
    output_json_grants = json.load(tmpdir.join('output_grant.json'))

    input_name = 'flattentool/tests/fixtures/xlsx/WellcomeTrust-grants_2_Grants.xlsx'
    unflatten(
        input_name=input_name,
        output_name=tmpdir.join('output_Grant.json').strpath,
        input_format='xlsx',
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        main_sheet_name='grants',
        root_list_path='grants',
        root_id='',
        convert_titles=True)
    output_json_Grants = json.load(tmpdir.join('output_Grant.json'))

    assert output_json_grants == output_json_Grants

def test_360_fields_case_insensitive(tmpdir):
    input_name = 'flattentool/tests/fixtures/xlsx/WellcomeTrust-grants_2_grants.xlsx'
    unflatten(
        input_name=input_name,
        output_name=tmpdir.join('output_grant.json').strpath,
        input_format='xlsx',
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        main_sheet_name='grants',
        root_list_path='grants',
        root_id='',
        convert_titles=True)
    output_json_grants = json.load(tmpdir.join('output_grant.json'))

    input_name = 'flattentool/tests/fixtures/xlsx/WellcomeTrust-grants_2_grants_title_space_case.xlsx'
    unflatten(
        input_name=input_name,
        output_name=tmpdir.join('output_space_case.json').strpath,
        input_format='xlsx',
        schema='flattentool/tests/fixtures/360-giving-schema.json',
        main_sheet_name='grants',
        root_list_path='grants',
        root_id='',
        convert_titles=True)
    output_json_space_case = json.load(tmpdir.join('output_space_case.json'))

    assert output_json_grants == output_json_space_case


def test_unflatten_xml(tmpdir):
    unflatten(
        input_name='examples/iati',
        output_name=tmpdir.join('output.xml').strpath,
        input_format='csv',
        root_list_path='iati-activity',
        id_name='iati-identifier',
        xml=True)
    assert open('examples/iati/expected.xml').read() == tmpdir.join('output.xml').read()
