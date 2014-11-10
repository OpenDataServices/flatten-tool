from __future__ import print_function
import argparse
from flattening_ocds import create_template, unflatten
from six import text_type


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output-name",
        help="Name of the outputted file. Will have an extension appended as appropriate. Defaults to release")
    subparsers = parser.add_subparsers(dest='subparser_name')

    parser_create_template = subparsers.add_parser(
        'create-template',
        help='Create a template from the given schema')
    parser_create_template.add_argument(
        "-s", "--schema",
        help="Path to the schema file you want to use to create the template",
        required=True)
    parser_create_template.add_argument(
        "-f", "--output-format",
        help="Type of template you want to create. Defaults to all available options")
    parser_create_template.add_argument(
        "-m", "--main-sheet-name",
        help="The name of the main sheet, as seen in the first tab of the spreadsheet for example. Defaults to main")

    parser_unflatten = subparsers.add_parser(
        'unflatten',
        help='Unflatten a spreadsheet')
    parser_unflatten.add_argument(
        'input_name',
        help="Name of the input file or directory.")
    parser_unflatten.add_argument(
        "-f", "--input-format",
        help="File format of input file or directory.",
        required=True)
    parser_unflatten.add_argument(
        "-b", "--base-json",
        help="A base json file to populate the releases key in.")
    parser_unflatten.add_argument(
        "-m", "--main-sheet-name",
        help="The name of the main sheet. Defaults to release")
    parser_unflatten.add_argument(
        "-e", "--encoding",
        help="Encoding of the input file(s) (only relevant for CSV). Defaults to utf8.")

    return parser


def kwargs_from_parsed_args(args):
    return {k: v for k, v in vars(args).items() if v is not None}


def main():
    """
    Takes any command line arguments and then passes them onto
    create_template
    Defaults are not set here, but rather given in the create_template
    function incase that function is called from elsewhere in future.
    """
    parser = create_parser()
    # Store the supplied arguments in args
    args = parser.parse_args()

    if args.subparser_name is None:
        parser.print_help()
    elif args.subparser_name == 'create-template':
        # Pass the arguments to the create_template function
        # If the schema file does not exist we catch it in this exception
        try:
            # Note: Ensures that empty arguments are not passed to the create_template function
            create_template(**kwargs_from_parsed_args(args))
        except (OSError, IOError) as e:
            print(text_type(e))
            return
    elif args.subparser_name == 'unflatten':
        unflatten(**kwargs_from_parsed_args(args))


if __name__ == '__main__':
    main()
