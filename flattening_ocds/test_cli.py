import pytest
from flattening_ocds import cli


def test_create_parser():
    """
    Command line arguments that should be acceptable
    """
    parser = cli.create_parser()
    #p.parse_args('cmd1 -b x three'.split())
    args = parser.parse_args('create-template -s schema.json'.split())
    #assert set(args.schema) == set(['schema', 'schema.json'])


def test_create_parser_missing_required_options():
    """
    If you do not supply certain arguments
    you should be warned
    """

    parser = cli.create_parser()
    #args = parser.parse_args()
    with pytest.raises(RuntimeError) as excinfo:
        args = parser.parse_args()
    assert 'invalid choice' in str(excinfo.value)
