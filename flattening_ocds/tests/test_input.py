from flattening_ocds.input import unflatten_line


def test_unflatten_line():
    # Check flat fields remain flat
    assert unflatten_line({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    assert unflatten_line({'a.b': 1, 'a.c': 2, 'd.e': 3}) == {'a': {'b': 1, 'c': 2}, 'd': {'e': 3}}
    # Check more than two levels of nesting, and that multicharacter fields aren't broken
    assert unflatten_line({'fieldA.b.c.d': 'value'}) == {'fieldA':{'b':{'c':{'d':'value'}}}}
