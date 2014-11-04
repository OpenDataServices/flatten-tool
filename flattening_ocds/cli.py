from __future__ import print_function
import argparse
from flattening_ocds import create_template


def main():
    """
    Takes any command line arguments and then passes them onto
    create_template
    Defaults are not set here, but rather given in the create_template
    function incase that function is called from elsewhere in future.
    """
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

    # Store the supplied arguments in args
    args = parser.parse_args()

    if args.subparser_name is None:
        parser.print_help()
    elif args.subparser_name == 'create-template':
        # Pass the arguments to the create_template function
        # If the schema file does not exist we catch it in this exception
        try:
            # Note: Ensures that empty arguments are not passed to the create_template function
            create_template(**{k: v for k, v in vars(args).items() if v is not None})
        except (OSError, IOError) as e:
            print(str(e))
            return


if __name__ == '__main__':
    main()
