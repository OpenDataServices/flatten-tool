from flattening_ocds.schema import SchemaParser
from flattening_ocds.output import FORMATS
from flattening_ocds.input import CSVInput, unflatten_spreadsheet_input
import json
from decimal import Decimal


def create_template(schema, output_name='release', output_format='all', main_sheet_name='main', **_):
    """
    Creates template file(s) from given inputs
    This function is built to deal with commandline input and arguments
    but to also be called from elswhere in future
    """

    parser = SchemaParser(schema_filename=schema, main_sheet_name=main_sheet_name)
    parser.parse()

    def spreadsheet_output(spreadsheet_output_class):
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name=main_sheet_name,
            output_name=output_name)
        spreadsheet_output.write_sheets()

    if output_format == 'all':
        for spreadsheet_output_class in FORMATS.values():
            spreadsheet_output(spreadsheet_output_class)

    elif output_format in FORMATS.keys():   # in dictionary of allowed formats
        spreadsheet_output(FORMATS[output_format])

    else:
        raise Exception("The requested format is not available")


# From http://bugs.python.org/issue16535
class number_str(float):
    def __init__(self, o):
        self.o = o

    def __repr__(self):
        return str(self.o)

    # This is needed for this trick to work in python 3.4
    def __float__(self):
        return self


def decimal_default(o):
    if isinstance(o, Decimal):
        return number_str(o)
    raise TypeError(repr(o) + " is not JSON serializable")


def unflatten(**_):
    spreadsheet_input = CSVInput(input_name='release_input', main_sheet_name='release')
    spreadsheet_input.read_sheets()
    with open('base.json') as fp:
        base = json.load(fp)
    base['releases'] = list(unflatten_spreadsheet_input(spreadsheet_input))
    print(json.dumps(base, indent=4, default=decimal_default))

