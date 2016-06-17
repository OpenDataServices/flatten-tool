Flattening
++++++++++

.. caution::

   This page is a work in progress. The information may not be complete, and
   unlike the Spreadsheet Designer's Guide, there are currently no tests backing
   up the documented examples. Use with caution.

So far, all the examples you've seen have been about unflattening - taking a
spreadsheet and producing a JSON document.

In this section you'll learn about flattening. The main use case for wanting to
flatten a JSON document is so that you can manage the data in a spreadsheet
from now on.

With that in mind there are two things you might want to do:

* Create an empty spreadsheet template ready to populate
* Unflatten a JSON document into a spreadsheet

Flatten Tool provides two sub-commands for these: `flatten-tool
create-template` and `flatten-tool flatten`.


Generating a spreadsheet template from a JSON Schema
====================================================

If you have a JSON Schema, Flatten Tool can produce some template spreadsheets
for you.

Here's an example command that uses a schema from the cafe example under `Sheet
shapes` and generates a spreadsheet:

.. code-block:: bash

    flatten-tool create-template --use-titles --main-sheet-name=cafe --schema=examples/receipt/cafe_and_tables.schema examples/cafe/tables-typed-schema/expected.json

The example uses `--use-titles` so that the generated spreadsheet has human
readable titles and `--main-sheet-name=cafe` so that the generated spreadsheet
have `cafe` as their first tab and not the default, `main`.

If you don't specify `-o`, Flatten Tool will choose a spreadsheet called
`template` in the current working directory.

If you don't specify a format, Flatten Tool will create a `template.xlsx` file
and a set of CSV files under `template/`.


Rolling up
----------

XXX Add an example.

If you have a JSON schema where objects are modeled as lists of objects but
actually represent one to one relationships, you can *roll up* certain
properties.

This means taking the values and rather than having them as a separate sheet,
have the values listed on the main sheet.

To enable roll up behaviour you have to:

* Use the `--rollup` flag

* Add the `rollUp` key to the JSON Schema to the child object with a value that
  is an array of the fields to roll up

Since all the examples so far are actually one-to-many relationships, there is
no example to demonstrate roll up on yet.

If you try to roll up multiple values you'll get a warning like this:

.. code-block:: bash

    .../flattentool/flattentool/json_input.py:152: UserWarning: More than one value supplied for "table". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.
      warn('More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'.format(parent_name+key))


Empty objects
-------------

If you have a JSON schema where an object's only property is an array
represented by another sheet, Flatten Tool will generate an empty sheet for the
object so that you can still add columns at a later date.


All create-template options
---------------------------

.. literalinclude:: ../examples/help/create-template/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/create-template/expected.txt
   :language: text


Generating a spreadsheet from a JSON document
=============================================

Generating a spreadsheet from a JSON document is very similar to creating a
template.

.. code-block:: bash

    flatten-tool flatten --use-titles --main-sheet-name=cafe --schema=examples/receipt/cafe_and_tables.schema examples/cafe/tables-typed-schema/expected.json

.. caution ::

   If you forget the `--root-list-path` option and your data isn't under a top
   level key called `main`, Flatten Tool won't find your data and will instead
   generate empty a single empty sheet called `main`, which probably isn't what
   you want.

This time the default output name is `flatten`, and so the command above will
generate a `flatten/` directory with CSV files and a `flatten.xlsx` file in the
current working directory.


All flatten options
-------------------

.. literalinclude:: ../examples/help/flatten/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/flatten/expected.txt
   :language: text
