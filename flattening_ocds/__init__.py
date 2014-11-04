from flattening_ocds.schema import SchemaParser
from flattening_ocds.output import FORMATS


def create_template(schema, output_name='release', output_format='all', main_sheet_name='main', **kwargs):
    """
    Creates template file(s) from given inputs
    This function is built to deal with commandline input and arguments
    but to also be called from elswhere in future
    """
    parser = SchemaParser(schema_filename=schema)
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
