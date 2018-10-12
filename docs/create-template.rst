Creating Templates
++++++++++++++++++

So far, all the examples you've seen have been about unflattening - taking a
spreadsheet and producing a JSON document.

If you already have a JSON schema, Flatten Tool can automatically create a
template spreadsheet with the correct headers that you can start filling in.

Flatten Tool's sub-command for this is `flatten-tool create-template`.


Generating a spreadsheet template from a JSON Schema
====================================================

Here's an example command that uses a schema from the cafe example under `Sheet
shapes` and generates a spreadsheet:

.. literalinclude:: ../examples/create-template/simple/cmd.txt
   :language: bash

The example uses `--use-titles` so that the generated spreadsheet has human
readable titles and `--main-sheet-name=cafe` so that the generated spreadsheet
have `cafe` as their first tab and not the default, `main`.

If you don't specify `-o`, Flatten Tool will choose a spreadsheet called
`template` in the current working directory.

If you don't specify a format with `-f`, Flatten Tool will create a
`template.xlsx` file and a set of CSV files under `template/`.

The schema is the same as the one used in the user guide and looks like this:

.. literalinclude:: ../examples/receipt/cafe.schema
   :language: json

If you run the example above, Flatten Tool will generate the following
CSV files for you:

.. csv-table:: sheet: cafe.csv
   :file: ../examples/create-template/simple/expected/cafe.csv

.. csv-table:: sheet: table.csv
   :file: ../examples/create-template/simple/expected/table.csv

.. csv-table:: sheet: tab_dish.csv
   :file: ../examples/create-template/simple/expected/tab_dish.csv

As you can see, by default Flatten Tool puts each item with an Identifier in
its own sheet.

Rolling up
----------

If you have a JSON schema where objects are modeled as lists of objects but
actually represent one to one relationships, you can *roll up* certain
properties.

This means taking the values and rather than having them as a separate sheet,
have the values listed on the main sheet.

To enable roll up behaviour you have to:

* Use the `--rollup` flag

* Add the `rollUp` key to the JSON Schema to the child object with a value that
  is an array of the fields to roll up

Here are the changes we make to the schema:

.. literalinclude:: ../examples/receipt/cafe-rollup.schema
   :diff: ../examples/receipt/cafe.schema

Here's the command we run:

.. literalinclude:: ../examples/create-template/rollup/cmd.txt
   :language: bash

Here are the resulting sheets:

.. csv-table:: sheet: cafe.csv
   :file: ../examples/create-template/rollup/expected/cafe.csv

.. csv-table:: sheet: table.csv
   :file: ../examples/create-template/rollup/expected/table.csv

.. csv-table:: sheet: tab_dish.csv
   :file: ../examples/create-template/rollup/expected/tab_dish.csv


Notice how `Table: Number` has now been moved into the `cafe.csv` file.

.. caution ::

   If you try to roll up multiple values you'll get a warning like this:

   .. code-block:: bash

       UserWarning: More than one value supplied for "table". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.
         warn('More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'.format(parent_name+key))


Empty objects
-------------

If you have a JSON schema where an object's only property is an array
represented by another sheet, Flatten Tool will generate an empty sheet for the
object so that you can still add columns at a later date.


Disable local refs
------------------

You can pass a `--disable-local-refs` flag for a special mode that will disable local refs in JSON Schema files.

.. literalinclude:: ../examples/create-template/refs-disable-local-refs/cmd.txt
   :language: bash

You may want to do this if running the command against JSON Schema files you don't trust.

All create-template options
---------------------------

.. literalinclude:: ../examples/help/create-template/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/create-template/expected.txt
   :language: text

