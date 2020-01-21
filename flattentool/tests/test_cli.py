import pytest
from flattentool import cli
# hint: test_argparse is provided by libpythonX.Y-testsuite on ubuntu
from test.test_argparse import stderr_to_parser_error, ArgumentParserError


def test_create_parser():
    """
    Command line arguments that should be acceptable
    """
    parser = cli.create_parser()
    args = parser.parse_args('create-template -s schema.json'.split())
    assert args.schema == 'schema.json'


def test_create_parser_missing_required_options():
    """
    If you do not supply certain arguments
    you should be warned
    """

    parser = cli.create_parser()
    with pytest.raises(ArgumentParserError) as excinfo:
        stderr_to_parser_error(parser.parse_args, 'create-template'.split())
    assert 'required' in excinfo.value.stderr
