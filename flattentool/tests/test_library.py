import json

import pytest

import flattentool


@pytest.fixture
def basic_data_1():
    """Example JSON data"""
    with open("flattentool/tests/fixtures/basic_1.json", "r") as read_file:
        return json.load(read_file)


@pytest.fixture
def bods_schema_0_3():
    """Example JSON schema"""
    with open("flattentool/tests/fixtures/schema-0-3-0.json", "r") as read_file:
        return json.load(read_file)


def test_unflatten_schema_as_filename(tmpdir, basic_data_1):
    output_file = "unflattened.json"
    unflatten_kwargs = {
        "output_name": tmpdir.join(output_file).strpath,
        "root_list_path": "there-is-no-root-list-path",
        "root_id": "statementID",
        "id_name": "statementID",
        "root_is_list": True,
        "input_format": "csv",
        "schema": "flattentool/tests/fixtures/schema-0-3-0.json",
    }

    flattentool.unflatten("flattentool/tests/fixtures/basic_1.csv", **unflatten_kwargs)

    output_json = json.load(tmpdir.join(output_file))

    for statement in output_json:
        statement_id = statement["statementID"]
        input_statement = [
            item for item in basic_data_1 if item["statementID"] == statement_id
        ][0]
        for property in statement:
            # Skip publicListing property since contains 'securitiesListings': [] and there is a
            # bug where empty lists are lost when flattening and then unflattening. This should
            # be fixed, see: https://github.com/OpenDataServices/flatten-tool/issues/470
            if property != "publicListing":
                assert statement[property] == input_statement[property]


def test_unflatten_schema_as_dict(tmpdir, basic_data_1, bods_schema_0_3):
    output_file = "unflattened.json"
    unflatten_kwargs = {
        "output_name": tmpdir.join(output_file).strpath,
        "root_list_path": "there-is-no-root-list-path",
        "root_id": "statementID",
        "id_name": "statementID",
        "root_is_list": True,
        "input_format": "csv",
        "schema": bods_schema_0_3,
    }

    flattentool.unflatten("flattentool/tests/fixtures/basic_1.csv", **unflatten_kwargs)

    output_json = json.load(tmpdir.join(output_file))

    for statement in output_json:
        statement_id = statement["statementID"]
        input_statement = [
            item for item in basic_data_1 if item["statementID"] == statement_id
        ][0]
        for property in statement:
            # Skip publicListing property since contains 'securitiesListings': [] and there is a
            # bug where empty lists are lost when flattening and then unflattening. This should
            # be fixed, see: https://github.com/OpenDataServices/flatten-tool/issues/470
            if property != "publicListing":
                assert statement[property] == input_statement[property]


def test_unflatten_schema_as_empty_dict(tmpdir, basic_data_1, bods_schema_0_3):
    output_file = "unflattened.json"
    unflatten_kwargs = {
        "output_name": tmpdir.join(output_file).strpath,
        "root_list_path": "there-is-no-root-list-path",
        "root_id": "statementID",
        "id_name": "statementID",
        "root_is_list": True,
        "input_format": "csv",
        "schema": {},  # Empty schema provided
    }

    flattentool.unflatten("flattentool/tests/fixtures/basic_1.csv", **unflatten_kwargs)

    output_json = json.load(tmpdir.join(output_file))

    for statement in output_json:
        statement_id = statement["statementID"]
        input_statement = [
            item for item in basic_data_1 if item["statementID"] == statement_id
        ][0]
        for property in statement:
            # Booleans, and integers should end up as strings because of empty schema
            if property in ("isComponent", "interests"):
                if isinstance(statement[property], list):
                    for sub_property in statement[property][0]:
                        if isinstance(statement[property][0][sub_property], dict):
                            for sub_sub_property in statement[property][0][
                                sub_property
                            ]:
                                assert isinstance(
                                    statement[property][0][sub_property][
                                        sub_sub_property
                                    ],
                                    str,
                                )
                        else:
                            assert isinstance(statement[property][0][sub_property], str)
                else:
                    assert isinstance(statement[property], str)
            # Skip publicListing property since contains 'securitiesListings': [] and there is a
            # bug where empty lists are lost when flattening and then unflattening. This should
            # be fixed, see: https://github.com/OpenDataServices/flatten-tool/issues/470
            elif property != "publicListing":
                assert statement[property] == input_statement[property]
