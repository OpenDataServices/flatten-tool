import json
import sys
import pytest
from io import StringIO, TextIOWrapper
from flattentool import cli
from test.test_argparse import stderr_to_parser_error, ArgumentParserError

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch


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


def test_stdin(tmpdir, monkeypatch):
    stdin = json.dumps({'main': [{'a': 1}]}, indent=4) + '\n'

    output_name = tmpdir.join('flattened').strpath + '.xlsx'

    with patch('sys.stdin', TextIOWrapper(StringIO(stdin))):
        monkeypatch.setattr(sys, 'argv', [
            'flatten-tool', 'flatten',
            '--output-name', output_name,
            '--output-format', 'xlsx',
        ])
        cli.main()

    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', [
            'flatten-tool', 'unflatten',
            '--input-format', 'xlsx',
            output_name,
        ])
        cli.main()

    assert actual.getvalue() == stdin
