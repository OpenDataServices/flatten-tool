"""
Test flattening (JSON input) by checking that we can run some of the unflatten
testdata in reverse.
"""

import json
from collections import OrderedDict

import pytest

from flattentool.json_input import JSONParser
from flattentool.schema import SchemaParser

from .test_input_SpreadsheetInput_unflatten import (
    ROOT_ID_PARAMS,
    create_schema,
    inject_root_id,
    testdata,
    testdata_titles,
)
from .test_input_SpreadsheetInput_unflatten_mulitplesheets import (
    testdata_multiplesheets,
    testdata_multiplesheets_titles,
)


# Don't test with use_titles and use_schema true because this will will use
# titles, which the fixtures don't
@pytest.mark.parametrize(
    "use_titles,use_schema", [(False, False), (True, False), (False, True)]
)
@pytest.mark.parametrize("root_id,root_id_kwargs", ROOT_ID_PARAMS)
@pytest.mark.parametrize(
    "comment,expected_output_list,input_list,warning_messages,reversible",
    [x[:5] for x in testdata if x[4]],
)
def test_flatten(
    use_titles,
    use_schema,
    root_id,
    root_id_kwargs,
    input_list,
    expected_output_list,
    recwarn,
    comment,
    warning_messages,
    tmpdir,
    reversible,
):
    # Not sure why, but this seems to be necessary to have warnings picked up
    # on Python 2.7 and 3.3, but 3.4 and 3.5 are fine without it
    import warnings

    warnings.simplefilter("always")

    extra_kwargs = {"use_titles": use_titles}
    extra_kwargs.update(root_id_kwargs)

    if use_schema:
        schema_parser = SchemaParser(
            root_schema_dict=create_schema(root_id)
            if use_schema
            else {"properties": {}},
            rollup=True,
            **extra_kwargs
        )
        schema_parser.parse()
    else:
        schema_parser = None

    with tmpdir.join("input.json").open("w") as fp:
        json.dump(
            {"mykey": [inject_root_id(root_id, input_row) for input_row in input_list]},
            fp,
        )

    parser = JSONParser(
        json_filename=tmpdir.join("input.json").strpath,
        root_list_path="mykey",
        schema_parser=schema_parser,
        **extra_kwargs
    )
    parser.parse()

    expected_output_list = [
        inject_root_id(root_id, expected_output_dict)
        for expected_output_dict in expected_output_list
    ]
    if expected_output_list == [{}]:
        # We don't expect an empty dictionary
        expected_output_list = []
    assert list(parser.main_sheet.lines) == expected_output_list


@pytest.mark.parametrize(
    "comment,expected_output_list,input_list,warning_messages,reversible",
    [x for x in testdata_titles if x[4]],
)
@pytest.mark.parametrize("root_id,root_id_kwargs", ROOT_ID_PARAMS)
def test_flatten_titles(
    root_id,
    root_id_kwargs,
    input_list,
    expected_output_list,
    recwarn,
    comment,
    warning_messages,
    reversible,
    tmpdir,
):
    """
    Essentially the same as test unflatten, except that convert_titles and
    use_schema are always true, as both of these are needed to convert titles
    properly. (and runs with different test data).
    """
    if root_id != "":
        # Skip all tests with a root ID for now, as this is broken
        # https://github.com/OpenDataServices/flatten-tool/issues/84
        pytest.skip()
    return test_flatten(
        use_titles=True,
        use_schema=True,
        root_id=root_id,
        root_id_kwargs=root_id_kwargs,
        input_list=input_list,
        expected_output_list=expected_output_list,
        recwarn=recwarn,
        comment=comment,
        warning_messages=warning_messages,
        reversible=reversible,
        tmpdir=tmpdir,
    )


# Don't test with use_titles and use_schema true because this will will use
# titles, which the fixtures don't
@pytest.mark.parametrize(
    "use_titles,use_schema", [(False, False), (True, False), (False, True)]
)
@pytest.mark.parametrize("root_id,root_id_kwargs", ROOT_ID_PARAMS)
@pytest.mark.parametrize(
    "comment,expected_output_dict,input_list,warning_messages,reversible",
    [x for x in testdata_multiplesheets if x[4]],
)
def test_flatten_multiplesheets(
    use_titles,
    use_schema,
    root_id,
    root_id_kwargs,
    input_list,
    expected_output_dict,
    recwarn,
    comment,
    warning_messages,
    tmpdir,
    reversible,
):
    # Not sure why, but this seems to be necessary to have warnings picked up
    # on Python 2.7 and 3.3, but 3.4 and 3.5 are fine without it
    import warnings

    warnings.simplefilter("always")

    extra_kwargs = {"use_titles": use_titles}
    extra_kwargs.update(root_id_kwargs)

    if use_schema:
        schema_parser = SchemaParser(
            root_schema_dict=create_schema(root_id)
            if use_schema
            else {"properties": {}},
            rollup=True,
            **extra_kwargs
        )
        schema_parser.parse()
    else:
        schema_parser = None

    with tmpdir.join("input.json").open("w") as fp:
        json.dump(
            {"mykey": [inject_root_id(root_id, input_row) for input_row in input_list]},
            fp,
        )

    parser = JSONParser(
        json_filename=tmpdir.join("input.json").strpath,
        root_list_path="mykey",
        schema_parser=schema_parser,
        **extra_kwargs
    )
    parser.parse()

    expected_output_dict = OrderedDict(
        [
            (sheet_name, [inject_root_id(root_id, line) for line in lines])
            for sheet_name, lines in expected_output_dict.items()
        ]
    )
    output = {
        sheet_name: sheet.lines
        for sheet_name, sheet in parser.sub_sheets.items()
        if sheet.lines
    }
    output["custom_main"] = parser.main_sheet.lines
    assert output == expected_output_dict


@pytest.mark.parametrize(
    "comment,expected_output_dict,input_list,warning_messages,reversible",
    [x for x in testdata_multiplesheets_titles if x[4]],
)
@pytest.mark.parametrize("root_id,root_id_kwargs", ROOT_ID_PARAMS)
def test_flatten_multiplesheets_titles(
    root_id,
    root_id_kwargs,
    input_list,
    expected_output_dict,
    recwarn,
    comment,
    warning_messages,
    reversible,
    tmpdir,
):
    """
    Essentially the same as test unflatten, except that convert_titles and
    use_schema are always true, as both of these are needed to convert titles
    properly. (and runs with different test data).
    """
    if root_id != "":
        # Skip all tests with a root ID for now, as this is broken
        # https://github.com/OpenDataServices/flatten-tool/issues/84
        pytest.skip()
    return test_flatten_multiplesheets(
        use_titles=True,
        use_schema=True,
        root_id=root_id,
        root_id_kwargs=root_id_kwargs,
        input_list=input_list,
        expected_output_dict=expected_output_dict,
        recwarn=recwarn,
        comment=comment,
        warning_messages=warning_messages,
        reversible=reversible,
        tmpdir=tmpdir,
    )
