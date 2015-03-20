from flattentool.schema import SchemaParser
from flattentool.json_input import JSONParser
from flattentool.output import FORMATS as OUTPUT_FORMATS
from flattentool.output import FORMATS_SUFFIX
from flattentool.input import FORMATS as INPUT_FORMATS
import json
from decimal import Decimal
from collections import OrderedDict


def create_template(schema, output_name='releases', output_format='all', main_sheet_name='main', flatten=False, rollup=False, root_id='ocid', use_titles=False, **_):
    """
    Creates template file(s) from given inputs
    This function is built to deal with commandline input and arguments
    but to also be called from elswhere in future
    """

    parser = SchemaParser(schema_filename=schema, main_sheet_name=main_sheet_name, rollup=rollup, root_id=root_id, use_titles=use_titles)
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


def flatten(input_name, schema=None, output_name='releases', output_format='all', main_sheet_name='main', root_list_path='releases', rollup=False, root_id='ocid', **_):
    if schema:
        schema_parser = SchemaParser(schema_filename=schema, rollup=rollup, root_id=root_id)
        schema_parser.parse()
    else:
        schema_parser = None
    parser = JSONParser(
        json_filename=input_name,
        root_list_path=root_list_path,
        schema_parser=schema_parser,
        main_sheet_name=main_sheet_name,
        root_id=root_id)
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


def unflatten(input_name, base_json=None, input_format=None, output_name='releases.json',
              main_sheet_name='releases', encoding='utf8', timezone_name='UTC',
              root_id='ocid', schema='', convert_titles=False, **_):
    if input_format is None:
        raise Exception('You must specify an input format (may autodetect in future')
    elif input_format not in INPUT_FORMATS:
        raise Exception('The requested format is not available')

    spreadsheet_input_class = INPUT_FORMATS[input_format]
    spreadsheet_input = spreadsheet_input_class(
        input_name=input_name,
        timezone_name=timezone_name,
        main_sheet_name=main_sheet_name,
        root_id=root_id,
        convert_titles=convert_titles)
    if convert_titles:
        parser = SchemaParser(schema_filename=schema, main_sheet_name=main_sheet_name, rollup=True, root_id=root_id)
        parser.parse()
        spreadsheet_input.parser = parser
    spreadsheet_input.encoding = encoding
    spreadsheet_input.read_sheets()
    if base_json:
        with open(base_json) as fp:
            base = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        base = OrderedDict()
    base[main_sheet_name] = list(spreadsheet_input.unflatten())
    with open(output_name, 'w') as fp:
        json.dump(base, fp, indent=4, default=decimal_default)

