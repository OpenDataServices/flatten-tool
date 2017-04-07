from flattentool.schema import SchemaParser
from flattentool.json_input import JSONParser
from flattentool.output import FORMATS as OUTPUT_FORMATS
from flattentool.output import FORMATS_SUFFIX
from flattentool.input import FORMATS as INPUT_FORMATS
from flattentool.xml_output import toxml
import sys
import json
import codecs
from decimal import Decimal
from collections import OrderedDict


def create_template(schema, output_name='template', output_format='all', main_sheet_name='main', flatten=False, rollup=False, root_id=None, use_titles=False, **_):
    """
    Creates template file(s) from given inputs
    This function is built to deal with commandline input and arguments
    but to also be called from elswhere in future

    """

    parser = SchemaParser(schema_filename=schema, rollup=rollup, root_id=root_id, use_titles=use_titles)
    parser.parse()

    def spreadsheet_output(spreadsheet_output_class, name):
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name=main_sheet_name,
            output_name=name)
        spreadsheet_output.write_sheets()

    if output_format == 'all':
        for format_name, spreadsheet_output_class in OUTPUT_FORMATS.items():
            spreadsheet_output(spreadsheet_output_class, output_name+FORMATS_SUFFIX[format_name])

    elif output_format in OUTPUT_FORMATS.keys():   # in dictionary of allowed formats
        spreadsheet_output(OUTPUT_FORMATS[output_format], output_name)

    else:
        raise Exception('The requested format is not available')


def flatten(input_name, schema=None, output_name='flattened', output_format='all', main_sheet_name='main', root_list_path='main', rollup=False, root_id=None, use_titles=False, **_):
    """
    Flatten a nested structure (JSON) to a flat structure (spreadsheet - csv or xlsx).

    """

    if schema:
        schema_parser = SchemaParser(
            schema_filename=schema,
            rollup=rollup,
            root_id=root_id,
            use_titles=use_titles)
        schema_parser.parse()
    else:
        schema_parser = None
    parser = JSONParser(
        json_filename=input_name,
        root_list_path=root_list_path,
        schema_parser=schema_parser,
        root_id=root_id,
        use_titles=use_titles)
    parser.parse()

    def spreadsheet_output(spreadsheet_output_class, name):
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name=main_sheet_name,
            output_name=name)
        spreadsheet_output.write_sheets()

    if output_format == 'all':
        for format_name, spreadsheet_output_class in OUTPUT_FORMATS.items():
            spreadsheet_output(spreadsheet_output_class, output_name+FORMATS_SUFFIX[format_name])

    elif output_format in OUTPUT_FORMATS.keys():   # in dictionary of allowed formats
        spreadsheet_output(OUTPUT_FORMATS[output_format], output_name)

    else:
        raise Exception('The requested format is not available')


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


def unflatten(input_name, base_json=None, input_format=None, output_name=None,
              root_list_path='main', encoding='utf8', timezone_name='UTC',
              root_id=None, schema='', convert_titles=False, cell_source_map=None,
              heading_source_map=None, id_name='id', xml=False,
              vertical_orientation=False,
              metatab_name=None, metatab_only=False, metatab_schema='',
              metatab_vertical_orientation=False,
              **_):
    """
    Unflatten a flat structure (spreadsheet - csv or xlsx) into a nested structure (JSON).

    """
    if input_format is None:
        raise Exception('You must specify an input format (may autodetect in future')
    elif input_format not in INPUT_FORMATS:
        raise Exception('The requested format is not available')
    if metatab_name and base_json:
        raise Exception('Not allowed to use base_json with metatab')

    if base_json:
        with open(base_json) as fp:
            base = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        base = OrderedDict()


    cell_source_map_data = OrderedDict()
    heading_source_map_data = OrderedDict()

    if metatab_name:
        spreadsheet_input_class = INPUT_FORMATS[input_format]
        spreadsheet_input = spreadsheet_input_class(
            input_name=input_name,
            timezone_name=timezone_name,
            root_list_path='meta',
            include_sheets=[metatab_name],
            convert_titles=convert_titles,
            vertical_orientation=metatab_vertical_orientation,
            id_name=id_name,
            xml=xml
        )
        if metatab_schema:
            parser = SchemaParser(schema_filename=metatab_schema)
            parser.parse()
            spreadsheet_input.parser = parser
        spreadsheet_input.encoding = encoding
        spreadsheet_input.read_sheets()
        result, cell_source_map_data_meta, heading_source_map_data_meta = spreadsheet_input.fancy_unflatten(
            with_cell_source_map=cell_source_map,
            with_heading_source_map=heading_source_map,
        )
        for key, value in (cell_source_map_data_meta or {}).items():
            ## strip off meta/0/ from start of source map as actually data is at top level
            cell_source_map_data[key[7:]] = value
        for key, value in (heading_source_map_data_meta or {}).items():
            ## strip off meta/ from start of source map as actually data is at top level
            heading_source_map_data[key[5:]] = value

        if result:
            base.update(result[0])

    if not metatab_only:
        spreadsheet_input_class = INPUT_FORMATS[input_format]
        spreadsheet_input = spreadsheet_input_class(
            input_name=input_name,
            timezone_name=timezone_name,
            root_list_path=root_list_path,
            root_id=root_id,
            convert_titles=convert_titles,
            exclude_sheets=[metatab_name],
            vertical_orientation=vertical_orientation,
            id_name=id_name,
            xml=xml
        )
        if schema:
            parser = SchemaParser(schema_filename=schema, rollup=True, root_id=root_id)
            parser.parse()
            spreadsheet_input.parser = parser
        spreadsheet_input.encoding = encoding
        spreadsheet_input.read_sheets()
        result, cell_source_map_data_main, heading_source_map_data_main = spreadsheet_input.fancy_unflatten(
            with_cell_source_map=cell_source_map,
            with_heading_source_map=heading_source_map,
        )
        cell_source_map_data.update(cell_source_map_data_main or {})
        heading_source_map_data.update(heading_source_map_data_main or {})
        base[root_list_path] = list(result)

    if xml:
        if output_name is None:
            if sys.version > '3':
                sys.stdout.buffer.write(toxml(base))
            else:
                sys.stdout.write(toxml(base))
        else:
            with codecs.open(output_name, 'wb') as fp:
                fp.write(toxml(base))
    else:
        if output_name is None:
            print(json.dumps(base, indent=4, default=decimal_default, ensure_ascii=False))
        else:
            with codecs.open(output_name, 'w', encoding='utf-8') as fp:
                json.dump(base, fp, indent=4, default=decimal_default, ensure_ascii=False)
    if cell_source_map:
        with codecs.open(cell_source_map, 'w', encoding='utf-8') as fp:
            json.dump(cell_source_map_data, fp, indent=4, default=decimal_default, ensure_ascii=False)
    if heading_source_map:
        with codecs.open(heading_source_map, 'w', encoding='utf-8') as fp:
            json.dump(heading_source_map_data, fp, indent=4, default=decimal_default, ensure_ascii=False)
