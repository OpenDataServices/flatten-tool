from flattening_ocds.schema import SchemaParser
from flattening_ocds.output import FORMATS


def main():
    parser = SchemaParser(schema_filename='release-schema.json')
    parser.parse()
    for spreadsheet_output_class in FORMATS.values():
        spreadsheet_output = spreadsheet_output_class(
            parser=parser,
            main_sheet_name='release')
        spreadsheet_output.write_sheets()


if __name__ == '__main__':
    main()
