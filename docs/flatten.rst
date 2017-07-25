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


All flatten options
-------------------

.. literalinclude:: ../examples/help/flatten/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/flatten/expected.txt
   :language: text
