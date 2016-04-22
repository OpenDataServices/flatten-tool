from flattentool.schema import SchemaParser
from flattentool.json_input import JSONParser
from flattentool.output import FORMATS as OUTPUT_FORMATS
from flattentool.output import FORMATS_SUFFIX
from flattentool.input import FORMATS as INPUT_FORMATS, WITH_CELLS
import json
import codecs
from decimal import Decimal
from collections import OrderedDict


def create_template(schema, output_name='template', output_format='all', main_sheet_name='main', flatten=False, rollup=False, root_id=None, use_titles=False, create_reference_tables=False, **_):
    """
    Creates template file(s) from given inputs
    This function is built to deal with commandline input and arguments
    but to also be called from elswhere in future

    """

    parser = SchemaParser(schema_filename=schema, rollup=rollup, root_id=root_id, use_titles=use_titles, create_reference_tables=create_reference_tables)
    parser.parse()

    def spreadsheet_output(spreadsheet_output_class, name):
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name=main_sheet_name,
            output_name=name,
            create_reference_tables=create_reference_tables)
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
        return NumberStr(o)
    raise TypeError(repr(o) + " is not JSON serializable")


def unflatten(input_name, base_json=None, input_format=None, output_name='unflattened.json',
              root_list_path='main', encoding='utf8', timezone_name='UTC',
              root_id=None, schema='', convert_titles=False, cell_source_map=None,
              heading_source_map=None, **_):
    """
    Unflatten a flat structure (spreadsheet - csv or xlsx) into a nested structure (JSON).

    """
    if input_format is None:
        raise Exception('You must specify an input format (may autodetect in future')
    elif input_format not in INPUT_FORMATS:
        raise Exception('The requested format is not available')

    spreadsheet_input_class = INPUT_FORMATS[input_format]
    spreadsheet_input = spreadsheet_input_class(
        input_name=input_name,
        timezone_name=timezone_name,
        root_list_path=root_list_path,
        root_id=root_id,
        convert_titles=convert_titles)
    if schema:
        parser = SchemaParser(schema_filename=schema, rollup=True, root_id=root_id)
        parser.parse()
        spreadsheet_input.parser = parser
    spreadsheet_input.encoding = encoding
    spreadsheet_input.read_sheets()
    if base_json:
        with open(base_json) as fp:
            base = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        base = OrderedDict()
    if WITH_CELLS:
        result, cell_source_map_data, heading_source_map_data = spreadsheet_input.fancy_unflatten()
        base[root_list_path] = list(result)
        with codecs.open(output_name, 'w', encoding='utf-8') as fp:
            json.dump(base, fp, indent=4, default=decimal_default, ensure_ascii=False)
        if cell_source_map:
            with codecs.open(cell_source_map, 'w', encoding='utf-8') as fp:
                json.dump(cell_source_map_data, fp, indent=4, default=decimal_default, ensure_ascii=False)
        if heading_source_map:
            with codecs.open(heading_source_map, 'w', encoding='utf-8') as fp:
                json.dump(heading_source_map_data, fp, indent=4, default=decimal_default, ensure_ascii=False)
    else:
        result = spreadsheet_input.unflatten()
        base[root_list_path] = list(result)
        with codecs.open(output_name, 'w', encoding='utf-8') as fp:
            json.dump(base, fp, indent=4, default=decimal_default, ensure_ascii=False)

