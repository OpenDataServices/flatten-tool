from __future__ import print_function

import argparse
import warnings
import sys

from six import text_type

from flattentool import create_template, unflatten, flatten
from flattentool.input import FORMATS as INPUT_FORMATS
from flattentool.output import FORMATS as OUTPUT_FORMATS
from flattentool.json_input import BadlyFormedJSONError

"""
This file does most of the work of the flatten-tool commandline command.

It takes any commandline arguments, and passes them to a function in
``__init__.py``.

It is callable via the ``flatten-tool`` executable in the directory below, or
using ``python -m flattentool.cli``.

"""


def create_parser():
    """
    Create an argparse ArgumentParser for our commandline arguments

    Defaults are not set here, but rather given in the appropriate function.

    (This is split out as it's own function primarily so it can be tested.)

    """

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser_name')

    output_formats = sorted(OUTPUT_FORMATS) + ['all']
    input_formats = sorted(INPUT_FORMATS)

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed output when warnings or errors occur.')

    parser_create_template = subparsers.add_parser(
        'create-template',
        help='Create a template from the given schema')
    parser_create_template.add_argument(
        "-s", "--schema",
        help="Path to the schema file you want to use to create the template",
        required=True)
    parser_create_template.add_argument(
        "-f", "--output-format",
        help="Type of template you want to create. Defaults to all available options",
        choices=output_formats)
    parser_create_template.add_argument(
        "-m", "--main-sheet-name",
        help="The name of the main sheet, as seen in the first tab of the spreadsheet for example. Defaults to main")
    parser_create_template.add_argument(
        "-o", "--output-name",
        help="Name of the outputted file. Will have an extension appended if format is all.")
    parser_create_template.add_argument(
        "--rollup",
        action='store_true',
        help="\"Roll up\" columns from subsheets into the main sheet if they are specified in a rollUp attribute in the schema.")
    parser_create_template.add_argument(
        "-r", "--root-id",
        help="Root ID of the data format, e.g. ocid for OCDS")
    parser_create_template.add_argument(
        "--use-titles",
        action='store_true',
        help="Convert titles.")
    parser_create_template.add_argument(
        "--disable-local-refs",
        action='store_true',
        help="Disable local refs when parsing JSON Schema.")
    parser_create_template.add_argument(
        "--no-deprecated-fields",
        action='store_true',
        help="Exclude Fields marked as deprecated in the JSON Schema.")
    parser_create_template.add_argument(
        "--truncation-length",
        type=int, default=3,
        help="The length of components of sub-sheet names (default 3).")

    parser_flatten = subparsers.add_parser(
        'flatten',
        help='Flatten a JSON file')
    parser_flatten.add_argument(
        'input_name',
        help="Name of the input JSON file.")
    parser_flatten.add_argument(
        "-s", "--schema",
        help="Path to a relevant schema.")
    parser_flatten.add_argument(
        "-f", "--output-format",
        help="Type of template you want to create. Defaults to all available options",
        choices=output_formats)
    parser_flatten.add_argument(
        "--xml",
        action='store_true',
        help="Use XML as the input format")
    parser_flatten.add_argument(
        "--id-name",
        help="String to use for the identifier key, defaults to 'id'")
    parser_flatten.add_argument(
        "-m", "--main-sheet-name",
        help="The name of the main sheet, as seen in the first tab of the spreadsheet for example. Defaults to main")
    parser_flatten.add_argument(
        "-o", "--output-name",
        help="Name of the outputted file. Will have an extension appended if format is all.")
    parser_flatten.add_argument(
        "--root-list-path",
        help="Path of the root list, defaults to main")
    parser_flatten.add_argument(
        "--rollup",
        nargs='?',
        const=True,
        action='append',
        help="\"Roll up\" columns from subsheets into the main sheet. Pass one or more JSON paths directly, or a file with one JSON path per line, or no value and use a schema containing (a) rollUp attribute(s). Schema takes precedence if both direct input and schema with rollUps are present.")
    parser_flatten.add_argument(
        "-r", "--root-id",
        help="Root ID of the data format, e.g. ocid for OCDS")
    parser_flatten.add_argument(
        "--use-titles",
        action='store_true',
        help="Convert titles. Requires a schema to be specified.")
    parser_flatten.add_argument(
        "--truncation-length",
        type=int, default=3,
        help="The length of components of sub-sheet names (default 3).")
    parser_flatten.add_argument(
        "--root-is-list",
        action='store_true',
        help="The root element is a list. --root-list-path and meta data will be ignored.")
    parser_flatten.add_argument(
        "--sheet-prefix",
        help="A string to prefix to the start of every sheet (or file) name.")
    parser_flatten.add_argument(
        "--filter-field",
        help="Data Filter - only data with this will be processed. Use with --filter-value")
    parser_flatten.add_argument(
        "--filter-value",
        help="Data Filter - only data with this will be processed. Use with --filter-field")
    parser_flatten.add_argument(
        "--preserve-fields",
        help="Only these fields will be processed. Pass a file with JSON paths to be preserved one per line.")
    parser_flatten.add_argument(
        "--disable-local-refs",
        action='store_true',
        help="Disable local refs when parsing JSON Schema.")
    parser_flatten.add_argument(
        "--remove-empty-schema-columns",
        action='store_true',
        help="When using flatten with a schema, remove columns and sheets from the output that contain no data.")

    parser_unflatten = subparsers.add_parser(
        'unflatten',
        help='Unflatten a spreadsheet')
    parser_unflatten.add_argument(
        'input_name',
        help="Name of the input file or directory.")
    parser_unflatten.add_argument(
        "-f", "--input-format",
        help="File format of input file or directory.",
        choices=input_formats,
        required=True)
    parser_unflatten.add_argument(
        "--xml",
        action='store_true',
        help="Use XML as the output format")
    parser_unflatten.add_argument(
        "--id-name",
        help="String to use for the identifier key, defaults to 'id'")
    parser_unflatten.add_argument(
        "-b", "--base-json",
        help="A base json file to populate with the unflattened data.")
    parser_unflatten.add_argument(
        "-m", "--root-list-path",
        help="The path in the JSON that will contain the unflattened list. Defaults to main.")
    parser_unflatten.add_argument(
        "-e", "--encoding",
        help="Encoding of the input file(s) (only relevant for CSV). This can be any encoding recognised by Python. Defaults to utf8.")
    parser_unflatten.add_argument(
        "-o", "--output-name",
        help="Name of the outputted file. Will have an extension appended as appropriate.")
    parser_unflatten.add_argument(
        "-c", "--cell-source-map",
        help="Path to write a cell source map to. Will have an extension appended as appropriate.")
    parser_unflatten.add_argument(
        "-a", "--heading-source-map",
        help="Path to write a heading source map to. Will have an extension appended as appropriate.")
    parser_unflatten.add_argument(
        "--timezone-name",
        help="Name of the timezone, defaults to UTC. Should be in tzdata format, e.g. Europe/London")
    parser_unflatten.add_argument(
        "-r", "--root-id",
        help="Root ID of the data format, e.g. ocid for OCDS")
    parser_unflatten.add_argument(
        "-s", "--schema",
        help="Path to a relevant schema.")
    parser_unflatten.add_argument(
        "--convert-titles",
        action='store_true',
        help="Convert titles. Requires a schema to be specified.")
    parser_unflatten.add_argument(
        "--vertical-orientation",
        action='store_true',
        help="Read spreadsheet so that headings are in the first column and data is read vertically. Only for XLSX not CSV")
    parser_unflatten.add_argument(
        "--metatab-name",
        help="If supplied will assume there is a metadata tab with the given name")
    parser_unflatten.add_argument(
        "--metatab-schema",
        help="The jsonschema of the metadata tab")
    parser_unflatten.add_argument(
        "--metatab-only",
        action='store_true',
        help="Parse the metatab and nothing else")
    parser_unflatten.add_argument(
        "--metatab-vertical-orientation",
        action='store_true',
        help="Read metatab so that headings are in the first column and data is read vertically. Only for XLSX not CSV")
    parser_unflatten.add_argument(
        "--xml-schema",
        dest='xml_schemas',
        metavar='XML_SCHEMA',
        nargs='*',
        help="Path to one or more XML schemas (used for sorting)")
    parser_unflatten.add_argument(
        "--default-configuration",
        help="Comma seperated list of default parsing commands for all sheets. Only for XLSX not CSV")
    parser_unflatten.add_argument(
        "--root-is-list",
        action='store_true',
        help="The root element is a list. --root-list-path and meta data will be ignored.")
    parser_unflatten.add_argument(
        "--disable-local-refs",
        action='store_true',
        help="Disable local refs when parsing JSON Schema.")
    parser_unflatten.add_argument(
        "--xml-comment",
        required=False,
        default="XML generated by flatten-tool",
        help="String comment of what generates the xml file")

    return parser


def kwargs_from_parsed_args(args):
    """
    Transforms argparse's parsed args object into a dictionary to be passed  as
    kwargs.

    """
    return {k: v for k, v in vars(args).items() if v is not None}


def non_verbose_error_handler(type, value, traceback):
    if type == BadlyFormedJSONError:
        sys.stderr.write('JSON error: {}\n'.format(value))
    else:
        sys.stderr.write(str(value) + '\n')


default_warning_formatter = warnings.formatwarning

def non_verbose_warning_formatter(message, category, filename, lineno, line=None):
    if issubclass(category, UserWarning):
        return str(message) + '\n'
    else:
        return default_warning_formatter(message, category, filename, lineno, line)


def main():
    """
    Use ``create_parser`` to get the commandline arguments, and pass them to
    the appropriate function in __init__.py (create_template, flatten or
    unflatten).

    """
    parser = create_parser()
    # Store the supplied arguments in args
    args = parser.parse_args()

    if args.subparser_name is None:
        parser.print_help()
        return

    if not args.verbose:
        sys.excepthook = non_verbose_error_handler
        warnings.formatwarning = non_verbose_warning_formatter

    if args.subparser_name == 'create-template':
        # Pass the arguments to the create_template function
        # If the schema file does not exist we catch it in this exception
        try:
            # Note: Ensures that empty arguments are not passed to the create_template function
            create_template(**kwargs_from_parsed_args(args))
        except (OSError, IOError) as e:
            print(text_type(e))
            return
    elif args.subparser_name == 'flatten':
        flatten(**kwargs_from_parsed_args(args))
    elif args.subparser_name == 'unflatten':
        unflatten(**kwargs_from_parsed_args(args))


if __name__ == '__main__':
    main()
