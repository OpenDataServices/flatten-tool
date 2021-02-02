import codecs
import json
import os
import sys
import tempfile
import uuid
from collections import OrderedDict
from decimal import Decimal

import jsonstreams
import zc.zlibstorage
import ZODB.FileStorage

from flattentool.input import FORMATS as INPUT_FORMATS
from flattentool.json_input import JSONParser
from flattentool.lib import parse_sheet_configuration
from flattentool.output import FORMATS as OUTPUT_FORMATS
from flattentool.output import FORMATS_SUFFIX
from flattentool.schema import SchemaParser
from flattentool.xml_output import toxml


def create_template(
    schema,
    output_name=None,
    output_format="all",
    main_sheet_name="main",
    rollup=False,
    root_id=None,
    use_titles=False,
    disable_local_refs=False,
    truncation_length=3,
    no_deprecated_fields=False,
    **_
):
    """
    Creates template file(s) from given inputs
    This function is built to deal with commandline input and arguments
    but to also be called from elsewhere in future

    """

    parser = SchemaParser(
        schema_filename=schema,
        rollup=rollup,
        root_id=root_id,
        use_titles=use_titles,
        disable_local_refs=disable_local_refs,
        truncation_length=truncation_length,
        exclude_deprecated_fields=no_deprecated_fields,
    )
    parser.parse()

    def spreadsheet_output(spreadsheet_output_class, name):
        spreadsheet_output = spreadsheet_output_class(
            parser=parser, main_sheet_name=main_sheet_name, output_name=name
        )
        spreadsheet_output.write_sheets()

    if output_format == "all":
        if not output_name:
            output_name = "template"
        for format_name, spreadsheet_output_class in OUTPUT_FORMATS.items():
            spreadsheet_output(
                spreadsheet_output_class, output_name + FORMATS_SUFFIX[format_name]
            )

    elif output_format in OUTPUT_FORMATS.keys():  # in dictionary of allowed formats
        if not output_name:
            output_name = "template" + FORMATS_SUFFIX[output_format]
        spreadsheet_output(OUTPUT_FORMATS[output_format], output_name)

    else:
        raise Exception("The requested format is not available")


def flatten(
    input_name,
    schema=None,
    output_name=None,
    output_format="all",
    main_sheet_name="main",
    root_list_path="main",
    root_is_list=False,
    sheet_prefix="",
    filter_field=None,
    filter_value=None,
    preserve_fields=None,
    rollup=False,
    root_id=None,
    use_titles=False,
    xml=False,
    id_name="id",
    disable_local_refs=False,
    remove_empty_schema_columns=False,
    truncation_length=3,
    **_
):
    """
    Flatten a nested structure (JSON) to a flat structure (spreadsheet - csv or xlsx).

    """

    if (filter_field is None and filter_value is not None) or (
        filter_field is not None and filter_value is None
    ):
        raise Exception("You must use filter_field and filter_value together")

    if schema:
        schema_parser = SchemaParser(
            schema_filename=schema,
            rollup=rollup,
            root_id=root_id,
            use_titles=use_titles,
            disable_local_refs=disable_local_refs,
            truncation_length=truncation_length,
        )
        schema_parser.parse()
    else:
        schema_parser = None

    with JSONParser(
        json_filename=input_name,
        root_list_path=None if root_is_list else root_list_path,
        schema_parser=schema_parser,
        rollup=rollup,
        root_id=root_id,
        use_titles=use_titles,
        xml=xml,
        id_name=id_name,
        filter_field=filter_field,
        filter_value=filter_value,
        preserve_fields=preserve_fields,
        remove_empty_schema_columns=remove_empty_schema_columns,
        truncation_length=truncation_length,
        persist=True,
    ) as parser:

        def spreadsheet_output(spreadsheet_output_class, name):
            spreadsheet_output = spreadsheet_output_class(
                parser=parser,
                main_sheet_name=main_sheet_name,
                output_name=name,
                sheet_prefix=sheet_prefix,
            )
            spreadsheet_output.write_sheets()

        if output_format == "all":
            if not output_name:
                output_name = "flattened"
            for format_name, spreadsheet_output_class in OUTPUT_FORMATS.items():
                spreadsheet_output(
                    spreadsheet_output_class, output_name + FORMATS_SUFFIX[format_name]
                )

        elif output_format in OUTPUT_FORMATS.keys():  # in dictionary of allowed formats
            if not output_name:
                output_name = "flattened" + FORMATS_SUFFIX[output_format]
            spreadsheet_output(OUTPUT_FORMATS[output_format], output_name)

        else:
            raise Exception("The requested format is not available")


# From http://bugs.python.org/issue16535
class NumberStr(float):
    def __init__(self, o):
        # We don't call the parent here, since we're deliberately altering it's functionality
        # pylint: disable=W0231
        self.o = o

    def __repr__(self):
        return str(self.o)

    # This is needed for this trick to work in python 3.4
    def __float__(self):
        return self


def decimal_default(o):
    if isinstance(o, Decimal):
        if int(o) == o:
            return int(o)
        else:
            return NumberStr(o)
    raise TypeError(repr(o) + " is not JSON serializable")


# This is to just to make ensure_ascii and default are correct for streaming library
class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, **kw):
        super().__init__(**kw)
        # overwrie these no matter the input to __init__
        self.ensure_ascii = False
        self.default=decimal_default


def unflatten(
    input_name,
    output_name=None,
    cell_source_map=None,
    root_is_list=False,
    xml=False,
    **kw
):

    zodb_db_location = (
        tempfile.gettempdir() + "/flattentool-" + str(uuid.uuid4())
    )
    zodb_storage = zc.zlibstorage.ZlibStorage(
        ZODB.FileStorage.FileStorage(zodb_db_location)
    )
    db = ZODB.DB(zodb_storage)



    json_stream_args = {"indent": 4,
                        "encoder": CustomJSONEncoder,
                        "close_fd": True}

    cell_source_map_stream = None
    output_stream = None

    if not xml:
        if root_is_list:
            json_stream_args['jtype'] = jsonstreams.Type.array
        else:
            json_stream_args['jtype'] = jsonstreams.Type.object

        if output_name:
            json_stream_args['fd'] = codecs.open(output_name, "w", encoding="utf-8")
        else:
            json_stream_args['fd'] = sys.stdout

        output_stream = jsonstreams.Stream(**json_stream_args)

    if cell_source_map:
        cell_source_map_file = codecs.open(cell_source_map, "w", encoding="utf-8")
        cell_source_map_stream = jsonstreams.Stream(jsonstreams.Type.object, filename=cell_source_map, indent=4, close_fd=True)

    try:
        _unflatten(
            input_name,
            output_name=output_name,
            root_is_list=root_is_list,
            xml=xml,
            cell_source_map=cell_source_map,
            output_stream=output_stream,
            cell_source_map_stream=cell_source_map_stream,
            db=db,
            **kw
        )
    finally:
        if output_stream:
            output_stream.close()
        if cell_source_map_stream:
            cell_source_map_stream.close()
        db.close()
        os.remove(zodb_db_location)
        os.remove(zodb_db_location + ".lock")
        os.remove(zodb_db_location + ".index")
        os.remove(zodb_db_location + ".tmp")


def _unflatten(
    input_name,
    base_json=None,
    input_format=None,
    output_name=None,
    root_list_path=None,
    root_is_list=False,
    encoding="utf8",
    timezone_name="UTC",
    root_id=None,
    schema="",
    convert_titles=False,
    cell_source_map=None,
    heading_source_map=None,
    id_name=None,
    xml=False,
    vertical_orientation=False,
    metatab_name=None,
    metatab_only=False,
    metatab_schema="",
    metatab_vertical_orientation=False,
    xml_schemas=None,
    default_configuration="",
    disable_local_refs=False,
    xml_comment=None,
    truncation_length=3,
    output_stream=None,
    cell_source_map_stream=None,
    db=None,
    **_
):
    """
    Unflatten a flat structure (spreadsheet - csv or xlsx) into a nested structure (JSON).

    """
    if input_format is None:
        raise Exception("You must specify an input format (may autodetect in future")
    elif input_format not in INPUT_FORMATS:
        raise Exception("The requested format is not available")
    if metatab_name and base_json:
        raise Exception("Not allowed to use base_json with metatab")

    if not root_is_list and base_json:
        with open(base_json) as fp:
            base = json.load(fp, object_pairs_hook=OrderedDict)
            for key, value in base.items():
                output_stream.write(key, value)

    base_configuration = parse_sheet_configuration(
        [item.strip() for item in default_configuration.split(",")]
    )

    cell_source_map_data = OrderedDict()
    heading_source_map_data = OrderedDict()

    if metatab_name and not root_is_list:
        spreadsheet_input_class = INPUT_FORMATS[input_format]
        spreadsheet_input = spreadsheet_input_class(
            input_name=input_name,
            timezone_name=timezone_name,
            root_list_path="meta",
            include_sheets=[metatab_name],
            convert_titles=convert_titles,
            vertical_orientation=metatab_vertical_orientation,
            id_name=id_name,
            xml=xml,
            use_configuration=False,
        )
        if metatab_schema:
            parser = SchemaParser(
                schema_filename=metatab_schema, disable_local_refs=disable_local_refs
            )
            parser.parse()
            spreadsheet_input.parser = parser
        spreadsheet_input.encoding = encoding
        spreadsheet_input.read_sheets()
        (
            result,
            cell_source_map_data_meta,
            heading_source_map_data_meta,
        ) = spreadsheet_input.fancy_unflatten(
            with_cell_source_map=cell_source_map,
            with_heading_source_map=heading_source_map,
        )
        for key, value in (cell_source_map_data_meta or {}).items():
            ## strip off meta/0/ from start of source map as actually data is at top level
            if cell_source_map_stream:
                cell_source_map_stream.write(key[7:], value)

        for key, value in (heading_source_map_data_meta or {}).items():
            ## strip off meta/ from start of source map as actually data is at top level
            heading_source_map_data[key[5:]] = value

        # update individual keys from base configuration
        base_configuration.update(
            spreadsheet_input.sheet_configuration.get(metatab_name, {})
        )

        if result:
            for key, value in result[0].items():
                output_stream.write(key, value)

    if root_list_path is None:
        root_list_path = base_configuration.get("RootListPath", "main")
    if id_name is None:
        id_name = base_configuration.get("IDName", "id")

    if not metatab_only or root_is_list:
        spreadsheet_input_class = INPUT_FORMATS[input_format]
        spreadsheet_input = spreadsheet_input_class(
            input_name=input_name,
            timezone_name=timezone_name,
            root_list_path=root_list_path,
            root_is_list=root_is_list,
            root_id=root_id,
            convert_titles=convert_titles,
            exclude_sheets=[metatab_name],
            vertical_orientation=vertical_orientation,
            id_name=id_name,
            xml=xml,
            base_configuration=base_configuration
        )
        if schema:
            parser = SchemaParser(
                schema_filename=schema,
                rollup=True,
                root_id=root_id,
                disable_local_refs=disable_local_refs,
                truncation_length=truncation_length,
            )
            parser.parse()
            spreadsheet_input.parser = parser
        spreadsheet_input.encoding = encoding
        spreadsheet_input.read_sheets()

        result = []

        if not root_is_list and not xml:
            list_stream = output_stream.subarray(root_list_path)
        else:
            list_stream = output_stream

        for (
                single_result,
                cell_source_map_data_main,
                heading_source_map_data_main,
            ) in spreadsheet_input.unflatten_with_storage(
                with_cell_source_map=cell_source_map,
                with_heading_source_map=heading_source_map,
                db=db
            ):

            if cell_source_map_stream and cell_source_map_data_main:
                for key, value in cell_source_map_data_main.items():
                    cell_source_map_stream.write(key, value)

            if xml:
                result.extend(single_result)
            else:
                for item in single_result:
                    list_stream.write(item)

            for key, value in (heading_source_map_data_main or {}).items():
                if key in heading_source_map_data:
                    for item in heading_source_map_data_main[key]:
                        if item not in heading_source_map_data[key]:
                            heading_source_map_data[key].append(item)
                else:
                    heading_source_map_data[key] = heading_source_map_data_main[key]

        if not root_is_list and not xml:
            list_stream.close()

    if xml:
        if root_is_list:
            base = result
        else:
            base = {}
            base[root_list_path] = result

        xml_root_tag = base_configuration.get("XMLRootTag", "iati-activities")
        xml_output = toxml(
            base,
            xml_root_tag,
            xml_schemas=xml_schemas,
            root_list_path=root_list_path,
            xml_comment=xml_comment,
        )
        if output_name is None:
            sys.stdout.buffer.write(xml_output)
        else:
            with codecs.open(output_name, "wb") as fp:
                fp.write(xml_output)

    if heading_source_map:
        with codecs.open(heading_source_map, "w", encoding="utf-8") as fp:
            json.dump(
                heading_source_map_data,
                fp,
                indent=4,
                default=decimal_default,
                ensure_ascii=False,
            )
