Flatten-Tool for BODS
=====================

flatten and unflatten
---------------------

This data standard has a list as the root element,
as opposed to other standards where the root element is a dict with meta data and a list of data.
When flattening and unflattening, use the `--root-is-list` option.

The id element is `statementID`, so also use the `--id-name` option.

.. code-block:: bash

    flatten-tool flatten -f csv --root-is-list --id-name=statementID -o examples/bods-one-flatten examples/bods-one.json
    flatten-tool unflatten -f csv --root-is-list --id-name=statementID -o examples/bods-one-unflattened.json examples/bods-one-flatten



