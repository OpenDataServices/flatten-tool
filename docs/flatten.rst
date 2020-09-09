.. _flattening:

Flattening
++++++++++

.. caution::

   This page is a work in progress. The information may not be complete, and
   unlike the :doc:`Spreadsheet Designer's Guide <unflatten>`, the tests backing
   up the documented examples are not correct. Use with caution.

The :doc:`Spreadsheet Designer's Guide <unflatten>` was about unflattening -
taking a spreadsheet and producing a JSON document.

In this section you'll learn about flattening. The main use case for wanting to
flatten a JSON document is so that you can manage the data in a spreadsheet.

Flatten Tool provides the ``flatten-tool flatten`` sub-command for this purpose.


Generating a spreadsheet from a JSON document
=============================================

Generating a spreadsheet from a JSON document is very similar to :doc:`creating
a template <create-template>`.

.. literalinclude:: ../examples/flatten/simple/cmd.txt
   :language: bash

One difference is that the default output name is ``flattened``, and so the
command above will generate a ``flattened/`` directory with CSV files and a
``flattened.xlsx`` file in the current working directory.

The schema is the same as the one used in the :doc:`user guide <unflatten>` and looks like this:

.. literalinclude:: ../examples/receipt/cafe.schema
   :language: json

The input JSON file looks like this:

.. literalinclude:: ../examples/receipt/normalised/expected.json
   :language: json

If you run the example above, Flatten Tool will generate the following
CSV files for you, populated with the data from the input JSON file.

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/simple/expected/cafe.csv
   :header-rows: 1

.. csv-table:: sheet: table.csv
   :file: ../examples/flatten/simple/expected/table.csv
   :header-rows: 1

.. csv-table:: sheet: tab_dish.csv
   :file: ../examples/flatten/simple/expected/tab_dish.csv

.. caution ::

   If you forget the ``--root-list-path`` option and your data isn't under a top
   level key called ``main``, Flatten Tool won't find your data and will instead
   generate a single empty sheet called ``main``, which probably isn't what you
   want.

If your data has a list as a root, use the ``--root-is-list`` option.

.. literalinclude:: ../examples/flatten/root-is-list/data.json
   :language: json

.. literalinclude:: ../examples/flatten/root-is-list/cmd.txt
   :language: bash

.. csv-table:: sheet: main.csv
   :file: ../examples/flatten/root-is-list/expected/main.csv

Sheet Prefix
------------

You can pass a string that will be added at the start of all CSV file names, or all Excel sheet names, using the ``--sheet-prefix`` option.


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

Currently, only simple filters can be specified using the ``--filter-field`` and ``--filter-value`` option.

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

No ``dishes`` sheet is produced, and the main sheet does not have a ``coffee`` column.

The field specified must be a field directly on the data object - it's not possible to filter on fields like ``pints/0/title`` .

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

Preserve Fields
---------------

By default, all fields in the input JSON are turned into columns in the CSV output. If you wish to keep only a subset of fields, you can pass the fields you want as a file using the ``preserve-fields`` option.

.. literalinclude:: ../examples/flatten/preserve-fields/input.json
   :language: json

.. literalinclude:: ../examples/flatten/preserve-fields/fields_to_preserve.csv
   :language: json

.. literalinclude:: ../examples/flatten/preserve-fields/cmd.txt
   :language: bash

.. csv-table:: sheet: main.csv
   :file: ../examples/flatten/preserve-fields/expected/main.csv
   :header-rows: 1

The input file should contain the full JSON paths of the fields you want to preserve, one per line. If any of the fields passed contain objects, all child fields will be preserved. Eg. if you pass `title`, the top level `title` fields will be preserved, but `dishes/title` will not; if you pass `dishes`, the `dishes/title` and any other children of `dishes` will automatically be preserved. If you pass `dishes` *and* `dishes/title`, *only* `dishes/title` will be preserved, other children of `dishes` will be excluded. The order of the fields in the input is not significant.

Rollup
------

If you have a JSON schema where objects are modeled as lists of objects but
actually represent one to one relationships, you can *roll up* certain
properties.

This means taking the values and rather than having them as a separate sheet,
have the values listed on the main sheet.

To enable roll up behaviour you have to:

* Use the ``--rollup`` flag

And do one of:

* Via schema: Add the ``rollUp`` key to the JSON Schema to the child object with a value that
  is an array of the fields to roll up
* Direct input: Pass one or more field at the command line
* File input: Pass a file with a line-separated list of fields

If you pass direct input or file input, *and* a schema which contains a ``rollUp`` attribute,
the schema is used and the direct input or file input are ignored.

However, if you pass direct or file input, *and* and a schema which *does not* contain a ``rollUp`` 
attribute, the direct or file input *will* be used.

For the following examples, we use this input data:

.. literalinclude:: ../examples/flatten/rollup/input.json
   :language: json

Here, the ``owners`` property contains a list with a single object. The ``dishes`` 
property is also a list of objects, but cannot be rolled up, as the cafe has more 
than one dish.

Rollup via schema
^^^^^^^^^^^^^^^^^

Here are the changes we make to the schema:

.. literalinclude:: ../examples/flatten/rollup/schema/cafe-rollup.schema
   :diff: ../examples/flatten/rollup/schema/cafe.schema

Here's the command we run:

.. literalinclude:: ../examples/flatten/rollup/schema/cmd.txt
   :language: bash

Here are the resulting sheets:

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/rollup/schema/expected/cafe.csv

.. csv-table:: sheet: Owners.csv
   :file: ../examples/flatten/rollup/schema/expected/Owner.csv

Notice how ``Owner: First name``, ``Owner: Last name`` and ``Owner: Email`` now 
appear in both the ``cafe.csv`` and ``Owner.csv`` files.

.. caution ::

   If you try to roll up multiple values you'll get a warning like this:

   .. code-block:: bash

       UserWarning: More than one value supplied for "dishes". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.
         warn('More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'.format(parent_name+key))

Rollup via direct input
^^^^^^^^^^^^^^^^^^^^^^^

Run this command to rollup all properties of the ``owners`` object:

.. literalinclude:: ../examples/flatten/rollup/direct/cmd.txt
   :language: bash

You can include multiple fields to rollup by passing ``--rollup`` multiple times:

.. code-block:: bash

   $ flatten-tool flatten --root-list-path=cafe --main-sheet-name=cafe --rollup=owners --rollup=dishes examples/flatten/rollup/input.json -o examples/flatten/rollup/direct/actual

For the result:

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/rollup/direct/expected/cafe.csv

Rollup via file input
^^^^^^^^^^^^^^^^^^^^^

Run this command to rollup all properties of the ``owners`` object:

.. literalinclude:: ../examples/flatten/rollup/file/cmd.txt
   :language: bash

Where the file contains:

.. literalinclude:: ../examples/flatten/rollup/file/fields_to_rollup.txt
   :language: bash

You can include multiple fields to rollup by passing ``--rollup`` multiple times:

For the result:

.. csv-table:: sheet: cafe.csv
   :file: ../examples/flatten/rollup/file/expected/cafe.csv

Selective rollup
^^^^^^^^^^^^^^^^

If you don't want to include all of the properties of a rolled up object in the main
sheet, you can use ``rollup`` in combination with ``preserve-fields``, eg.

.. code-block:: bash

   $ flatten-tool flatten --root-list-path=cafe --main-sheet-name=cafe --rollup=owners --preserve-fields fields-to-preserve.txt examples/flatten/rollup/input.json -o examples/flatten/rollup/direct/actual

Where ``fields-to-preserve.txt`` contains:

.. code-block:: bash
   
   id
   type
   title
   owners/email

This excludes ``owners/firstname`` and ``owners/lastname`` from *both* the main sheet 
and the owners sheet.

All flatten options
-------------------

.. literalinclude:: ../examples/help/flatten/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/flatten/expected.txt
   :language: text
