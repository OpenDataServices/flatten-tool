Flattening
++++++++++

.. caution::

   This page is a work in progress. The information may not be complete, and
   unlike the Spreadsheet Designer's Guide, the tests backing
   up the documented examples are not correct. Use with caution.

So far, all the examples you've seen have been about unflattening - taking a
spreadsheet and producing a JSON document.

In this section you'll learn about flattening. The main use case for wanting to
flatten a JSON document is so that you can manage the data in a spreadsheet
from now on.

Flatten Tool provides `flatten-tool flatten` sub-command for this purpose.


Generating a spreadsheet from a JSON document
=============================================

Generating a spreadsheet from a JSON document is very similar to creating a
template.

.. literalinclude:: ../examples/flatten/simple/cmd.txt
   :language: bash

One difference is that the default output name is `flatten`, and so the command
above will generate a `flatten/` directory with CSV files and a `flatten.xlsx`
file in the current working directory.

The schema is the same as the one used in the user guide and looks like this:

.. literalinclude:: ../examples/receipt/cafe.schema
   :language: json

The input JSON file looks like this:

.. literalinclude:: ../examples/receipt/normalised/expected.json
   :language: json

If you run the example above, Flatten Tool will generate the following
CSV files for you, populated with the data from the input JSON file.

.. warning ::

   You can't use `--use-titles` with flatten.

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/simple/expected/cafe.csv
   :header-rows: 1

.. csv-table:: sheet: table.csv
   :file: ../examples/flatten/simple/expected/table.csv
   :header-rows: 1

.. csv-table:: sheet: tab_dish.csv
   :file: ../examples/flatten/simple/expected/tab_dish.csv

.. caution ::

   If you forget the `--root-list-path` option and your data isn't under a top
   level key called `main`, Flatten Tool won't find your data and will instead
   generate empty a single empty sheet called `main`, which probably isn't what
   you want.

If your data has a list as a root, use the `--root-is-list` option.

.. literalinclude:: ../examples/flatten/root-is-list/data.json
   :language: json

.. literalinclude:: ../examples/flatten/root-is-list/cmd.txt
   :language: bash

.. csv-table:: sheet: main.csv
   :file: ../examples/flatten/root-is-list/expected/main.csv

Sheet Prefix
------------

You can pass a string that will be added at the start of all CSV file names, or all Excel sheet names.


.. literalinclude:: ../examples/flatten/sheet-prefix/cmd.txt
   :language: bash

Will produce:

.. csv-table:: sheet: test-cafe.csv
   :file: ../examples/flatten/sheet-prefix/expected/test-cafe.csv
   :header-rows: 1

.. csv-table:: sheet: test-table.csv
   :file: ../examples/flatten/sheet-prefix/expected/test-table.csv
   :header-rows: 1

.. csv-table:: sheet: test-tab_dish.csv
   :file: ../examples/flatten/sheet-prefix/expected/test-tab_dish.csv

Filter
------

When flattening, you can optionally choose to only process some of the data.

Currently, only simple filters can be specified using the `--filter-field` and `--filter-value` option.

.. literalinclude:: ../examples/flatten/filter/input.json
   :language: json

.. literalinclude:: ../examples/flatten/filter/cmd.txt
   :language: bash

.. csv-table:: sheet: main.csv
   :file: ../examples/flatten/filter/expected/main.csv
   :header-rows: 1

.. csv-table:: sheet: pints.csv
   :file: ../examples/flatten/filter/expected/pints.csv
   :header-rows: 1

No `dishes` sheet is produced, and the main sheet does not have a `coffee` column.

The field specified must be a field directly on the data object - it's not possible to filter on fields like `pints/0/title` .

Remove Empty Schema Columns
---------------------------

By default, when using this with `schema` specified columns that are empty (have no data) will be kept in the output.

But you can pass the `remove-empty-schema-columns` flag to have these removed.

If all columns are removed from a sheet and it is empty, the whole sheet will be removed too.

This shows without and with the flag:

.. literalinclude:: ../examples/flatten/simple/cmd.txt
   :language: bash

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/simple/expected/cafe.csv
   :header-rows: 1

.. literalinclude:: ../examples/flatten/remove-empty-schema-columns/cmd.txt
   :language: bash

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/remove-empty-schema-columns/expected/cafe.csv
   :header-rows: 1

(Using this without the `schema` option does nothing.)


All flatten options
-------------------

.. literalinclude:: ../examples/help/flatten/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/flatten/expected.txt
   :language: text
