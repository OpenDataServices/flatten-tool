Spreadsheet Designer's Guide
++++++++++++++++++++++++++++

In this guide you'll learn the various rules Flatten Tool uses to convert one
or more sheets in a spreadsheet into a JSON document. These rules are
documented with examples based around a cafe theme.

Once you've understood how Flatten Tool works you should be able to design your
own spreadsheet structures, debug problems in your spreadsheets and be able to
make use of Flatten Tool's more advanced features.

Before we get into too much detail though, let's start by looking
at the Command Line API for unflattening a spreadsheet.


Command Line API
================

To demonstrate the command line API you'll start with the simplest possible
example, a sheet listing Cafe names:

.. csv-table::
   :file: ../examples/cafe/too-simple/data.csv
   :header-rows: 1

We'd like Flatten Tool to convert it to the following JSON structure for an array
of cafes, with the cafe name being the only property we want for each cafe:

.. literalinclude:: ../examples/cafe/simple/expected.json
   :language: json

Let's try converting the sheet to the JSON above.

.. literalinclude:: ../examples/cafe/too-simple/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/too-simple/expected.json
   :language: json

That's not too far off what we wanted. You can see the array of cafes, but the
key is named ``main`` instead of ``cafe``.  You can tell Flatten Tool that that the
rows in the spreadsheet are cafes and should come under a ``cafe`` key by
specifying a *root list path*, described next.

.. caution::

   Older Python versions add a trailing space after ``,`` characters when
   outputting indented JSON. This means that your output might have whitespace
   differences compared to what is described here.

Root List Path
--------------

The *root list path* is the key under which Flatten Tool should add an array of
objects representing each row of the main sheet.

You specify the root list path with ``--root-list-path`` option. If you don't
specify it, ``main`` is used as the default as you saw in the last example.

Let's set ``--root-list-path`` to ``cafe`` so that our original input generates the
JSON we were expecting:

.. literalinclude:: ../examples/cafe/simple/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/simple/expected.json
   :language: json

That's what we expected. Great.

.. note::

    Although ``--root-list-path`` sounds like it accepts a path such as
    ``building/cafe``, it only accepts a single key.


The root is a list
------------------

You can also specify the data outputted is just a list, using the ``--root-is-list`` option.

.. literalinclude:: ../examples/cafe/root-is-list/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/root-is-list/expected.json
   :language: json


Writing output to a file
------------------------

By default, Flatten Tool prints its output to stdout. If you want it to write
its output to a file instead, you can use the ``-o`` option.

Here's the same example, this time writing its output to ``unflattened.json``:

.. literalinclude:: ../examples/cafe/simple-file/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/simple-file/expected.json
   :language: json


Base JSON
---------

If you want the resulting JSON to also include other keys that you know in
advance, you can specify them in a separate *base JSON* file and Flatten Tool
will merge the data from your spreadsheet into that file.

For example, if ``base.json`` looks like this:

.. literalinclude:: ../examples/cafe/simple-base-json/base.json
   :language: json

and the data looks like this:

.. csv-table::
   :file: ../examples/cafe/simple-base-json/data.csv
   :header-rows: 1

you can run this command using the ``--base-json`` option to see the ``base.json``
data with the with the spreadsheet rows merged in:

.. literalinclude:: ../examples/cafe/simple-base-json/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/simple-base-json/expected.json
   :language: json

.. warning::

   If you give the base JSON the same key as you specify in ``--root-list-path``
   then Flatten Tool will overwrite its value.


All unflatten options
---------------------

You can see all the options available for unflattening by running:

.. literalinclude:: ../examples/help/unflatten/cmd.txt
   :language: bash
.. literalinclude:: ../examples/help/unflatten/expected.txt
   :language: text

As you can see, some of the documentation is specific to two projects that
use Flatten Tool:

* OCDS - http://standard.open-contracting.org/validator/
* 360Giving - http://www.threesixtygiving.org/standard/reference/

Other options such as ``--cell-source-map`` and ``--heading-source-map`` will be
described in the Developer Guide once the features stabilise.


Understanding JSON Pointer and how Flatten Tool uses it
=======================================================

Let's consider this data again and explore the algorithm Flatten Tool
uses to make it work:

.. csv-table::
   :file: ../examples/cafe/simple/data.csv
   :header-rows: 1

Here's a command to unflatten it and the resulting JSON:

.. literalinclude:: ../examples/cafe/simple/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/simple/expected.json
   :language: json

The key to understanding how Flatten Tool represents more complex examples in a
spreadsheet lies in knowing about the `JSON Pointer specification
<https://tools.ietf.org/html/rfc6901>`_.  This specification describes a fairly
intuitive way to reference values in a JSON document.

To briefly describe how it works, each ``/`` character after the first one drills
down into a JSON structure. If they value after the ``/`` is a string, then a key
is looked up, if it is an integer then an array index is taken.

For example, in the JSON pointer ``/cafe/0/name`` is equivalent to taking the
following value out of a JSON document named ``document``:

.. code-block:: python

    >>> document['cafe'][0]['name']

In JSON document above, the JSON pointer ``/cafe/0/name`` would return ``Healthy Cafe``.

.. note::

   JSON pointer array indexes start at 0, just like lists in Python, hence the
   first cafe is at index 0.

Whilst JSON pointer is designed as a way for getting data *out* of a JSON
document, Flatten Tool uses JSON Pointer as a way of describing how to move
values *into* a JSON document from a spreadsheet.

To do this, as it comes across JSON pointers, it automatically creates the
objects and arrays required.

You can think of Flatten Tool doing the following as it parses a sheet:

* Load the base JSON or use an empty JSON object

* For each row:

   * Convert each column heading to a JSON pointer by removing whitespace and
     prepending with ``/cafe/``, then adding the row index and another ``/`` to the
     front

   * Take the value in each column and associate it with the JSON pointer
     (treating any numbers as array indexes, and overwriting existing JSON pointer
     values for that row if necessary)

   * Write the value into the position in the JSON object being specified by the
     JSON pointer, creating more structures as you go

In this example there is only one sheet, and only one row, so when parsing that
first row, ``/cafe/0/`` is appended to ``name`` to give the JSON pointer
``/cafe/0/name``. Flatten Tool then writes ``Healthy Cafe`` in the correct position.


Index behaviour
---------------

There is one subtlety you need to be aware of though before you see some examples.

Although Flatten Tool always uses strings in a JSON pointer as object keys, it
only takes numbers it comes across as an *indication* of the array position.

For example, if you gave it the JSON pointer ``/cafe/1503/name``, there is no
guarantee that the ``name`` would be placed in an object at index position 1503.

Instead Flatten Tool uses numbers in the same sheet that are at the same parent
JSON pointer path (``/cafe/`` in this case), as being the sort order the child
objects should appear in, but not the literal index positions.

If two objects use the same index at the same base JSON pointer path, Flatten
Tool will keep both but the one it comes across first will come before the
other.

This behaviour has two advantages:

* data won't be lost if for some reason the index wasn't specified correctly

* the data in the generated JSON will be in the same order as it was specified
  in the sheets which is likely to be what the person putting data into the
  spreadsheet would expect

This behaviour is also important when you learn about Lists of Objects (without
IDs) later.

.. tip::

   You'll see later in the relationships section, that special ``id`` values can
   alter the index behavior described here and allow Flatten Tool to merge rows
   from multiple sheets.


Multiple rows
-------------

Let's look at a multi-row example:

.. csv-table::
   :file: ../examples/cafe/simple-row/data.csv
   :header-rows: 1

This time ``Healthy Cafe`` would be placed at ``/cafe/0/name`` and ``Vegetarian
Cafe`` at ``/cafe/1/name`` producing this:

.. literalinclude:: ../examples/cafe/simple-row/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/simple-row/expected.json
   :language: json

Although both ``Healthy Cafe`` and ``Vegetarian Cafe`` are under a column that
resolves to ``/cafe/0/name``, the rules described in the previous section explain
why both are present in the output and why ``Healthy Cafe`` comes before
``Vegetarian Cafe``.


Multiple columns
----------------

Let's add the cafe address to the spreadsheet:

.. csv-table::
   :header-rows: 1
   :file: ../examples/cafe/simple-col/data.csv

.. note::

   CSV files require cells containing ``,`` characters to be escaped by wrapping
   them in double quotes. That's why if you look at the source CSV, the addresses
   are escaped with ``"`` characters.

This time ``Healthy Cafe`` is placed at ``/cafe/0/name`` as before, ``London`` is
placed at ``/cafe/0/address``. ``Vegetarian Cafe`` at ``/cafe/1/name`` as before and
``Bristol`` is at ``/cafe/1/address``.

The result is:

.. literalinclude:: ../examples/cafe/simple-col/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/simple-col/expected.json
   :language: json


Multiple sheets
---------------

So far, all the examples have just used one sheet. When multiple sheets are
involved, the behaviour isn't much different.

In effect, all Flatten Tool does is:

* take the JSON structure produced after processing the previous sheets and use
  it as the base JSON for processing the next sheet

* keep track of the index numbers of existing objects and generate JSON
  pointers that point to the next free index at any existing locations (with the
  effect of having new objects appended to any existing ones at the same
  location)

Once all the sheets have been processed the resulting JSON is returned.

.. note::

   The CSV specification doesn't support multiple sheets. To work around this,
   Flatten Tool treats a directory of CSV files as a single spreadsheet with
   multiple sheets - one for each file.

   This is why all the CSV file examples given so far have been written to a
   file in an empty directory and why only the directory name was needed in
   the ``flatten-tool`` commands.

Here's a simple two-sheet example where the headings are the same in both
sheets:

.. csv-table:: sheet: data
   :file: ../examples/cafe/multiple/data.csv
   :header-rows: 1

.. csv-table:: sheet: other
   :file: ../examples/cafe/multiple/other.csv
   :header-rows: 1

When you run the example you get this:

.. literalinclude:: ../examples/cafe/multiple/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/multiple/expected.json
   :language: json

The order is because the ``data`` sheet was processed before the ``other`` sheet.

.. tip::

    CSV file sheets are processed in the order returned by ``os.listdir()`` so
    you should name them in the order you would like them processed.


Objects
=======

Now you know that the column headings are really just a JSON Pointer
specification, and the index values are only treated as indicators of the
presence of arrays you can write some more sophisticated examples.

Rather than have the address just as string, we could represent it as an
object. For example, imagine you'd like out output JSON in this structure:

.. literalinclude:: ../examples/cafe/object/expected.json
   :language: json

You can do this by knowing that the JSON Pointer to "123 City Street" would be
``/cafe/0/address/street`` so that we would need to name the street column
``address/street``.

Here's the data:

.. csv-table::
   :file: ../examples/cafe/object/data.csv
   :header-rows: 1

Let's try it:

.. literalinclude:: ../examples/cafe/object/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/object/expected.json
   :language: json


Lists of Objects (without IDs)
==============================

The cafe's that have made up our examples so far also have tables, and the
tables have a table number so that the waiters know where the food has to be
taken to.

Each cafe has many tables, so this is an example of a one-to-many relationship
if you are used to working with relational databases.

You can represent the table information in JSON as a array of objects, where each
object represents a table, and each table has a ``number`` key. Let's imagine the
``Healthy Cafe`` has three tables numbered 1, 2 and 3. We'd like to produce this
structure:

.. literalinclude:: ../examples/cafe/list-of-objects/expected.json
   :language: json

In the relationships section later, we'll see other (often better) ways of
arranging this data using *identifiers*, but for now we'll demonstrate an
approach that puts all the table information in the same row as the cafe
itself.

For example, consider this spreadsheet data:

.. csv-table::
   :file: ../examples/cafe/one-table/data.csv
   :header-rows: 1

.. literalinclude:: ../examples/cafe/list-of-objects/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/list-of-objects/expected.json
   :language: json

We'll use this example of tables (of the furniture variety) in subsequent
examples.


Index behaviour
---------------

Just as in the multiple sheets example earlier, the exact numbers at the table
index positions aren't too important to Flatten Tool. They just tell Flatten
Tool that the value in the cell is part of an object in an array.

In this particular case though, Flatten Tool will keep columns in order implied
by the indexes.

For example here the index values are such that the lowest number comes last:

.. csv-table::
   :file: ../examples/cafe/tables-index/data.csv
   :header-rows: 1

We'd still expect 3 tables in the output, but we expect Flatten Tool to
re-order the columns so that table 3 comes first, then 2, then 1:

.. literalinclude:: ../examples/cafe/tables-index/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/tables-index/expected.json
   :language: json

Child objects like these tables can, of course have more than one key. Let's
add a ``reserved`` key to table number 1 but to try to confuse Flatten Tool,
we'll specify it at the end:

.. csv-table::
   :file: ../examples/cafe/tables-index-reserved/data.csv
   :header-rows: 1

.. literalinclude:: ../examples/cafe/tables-index-reserved/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/tables-index-reserved/expected.json
   :language: json

Notice that Flatten Tool correctly associated the ``reserved`` key with table 1
because of the index numbered ``30``, even though the columns weren't next to
each other.

For a much richer way of organising arrays of objects, see the Relationships
section.


Plain Lists (Unsupported)
-------------------------

Flatten Tool doesn't support arrays of JSON values other than objects (just
described in the previous section).

As a result heading names such as ``tag/0`` and ``tag/1`` would be ignored and an
empty array would be put into the JSON.

Here's some example data:

.. csv-table::
   :file: ../examples/cafe/plain-list/data.csv
   :header-rows: 1

And the result:

.. literalinclude:: ../examples/cafe/plain-list/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/plain-list/expected.json
   :language: json


Typed fields
============

In the table examples you've seen so far, the table numbers are produced as
strings in the JSON. The JSON Pointer specification doesn't provide any way of
telling you what type the value being pointed to is, so we can't get the
information from the column headings.

There are two places we can get it from though:

* The spreadsheet cell (if the underlying spreadsheet type supports it, e.g.
  CSV doesn't but XLSX does)
* An external JSON Schema describing the data

If we can't get any type information we fall back to assuming strings.

Here is the sample data we'll use for the examples in the next two sections:

.. csv-table::
   :file: ../examples/cafe/tables-typed-schema/data.csv
   :header-rows: 1


Using spreadsheet cell formatting
---------------------------------

CSV files only support string values, so the easiest way to get the example
above to use integers would be to use a spreadsheet format such as XLSX that
supported integers and make sure the cell type was number. Flatten Tool would
pass the cell value through to the JSON as a number in that case.

.. note::

    Make sure you specify the correct format ``-f=xlsx`` on the command line if
    you want to use an XLSX file.

.. literalinclude:: ../examples/cafe/tables-typed-xlsx/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/tables-typed-xlsx/expected.json
   :language: json

.. caution::

   Number formats in spreadsheets are ignored in Python 2.7 so this
   example won't work. It does work in Python 3.4 and above though.

   If you look at Flatten Tool's source code you'll see the in ``test_docs.py``
   that the above example is skipped on older Python versions.


Using a JSON Schema with types
------------------------------

Here's an example of a JSON Schema that can provide the typing information:

.. literalinclude:: ../examples/cafe/tables-typed-schema/cafe.schema
   :language: json

.. literalinclude:: ../examples/cafe/tables-typed-schema/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/tables-typed-schema/expected.json
   :language: json

.. tip::

   Although this example is too simple to demonstrate it, Flatten Tool ignores
   the order of individual properties in a JSON schema when producing JSON output,
   and instead follows the order of the columns in the sheets.


Human-friendly headings using a JSON Schema with titles
=======================================================

Let's take a closer look at the array of objects example from earlier again:

.. csv-table::
   :file: ../examples/cafe/list-of-objects/data.csv
   :header-rows: 1

The column headings ``table/0/number``, ``table/1/number`` and ``table/2/number``
aren't very human readable, wouldn't it be great if we could use headings like
this:

.. csv-table::
   :file: ../examples/cafe/tables-human-1/data.csv
   :header-rows: 1

Flatten Tool supports this if you do the following:

* Write a JSON Schema specifying the titles being used and
  specify it with the ``--schema`` option
* Use ``:`` characters instead of ``/`` characters in the headings
* Specify the ``--convert-titles`` option on the command line

.. caution::

   If you forget any of these, Flatten Tool might produce incorrect JSON rather
   than failing.

Here's a new JSON schema for this example:

.. literalinclude:: ../examples/cafe/tables-human-1/cafe.schema
   :language: json

Notice that both ``Table`` and ``Number`` are specified as titles.

Here's what we get when we run it:

.. literalinclude:: ../examples/cafe/tables-human-1/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/tables-human-1/expected.json
   :language: json


Optional array indexes
----------------------

Looking at the JSON Schema from the last example again you'll see that ``table``
is specified as an array type:

.. literalinclude:: ../examples/cafe/tables-human-2/cafe.schema
   :language: json

This means that Flatten Tool can work out that any names specified in that
column are part of that array. If you had an example with just one column
representing each level of the tree, you could miss out the index in the
heading when using ``--schema`` and ``--convert-titles``.

Here's a similar example, but with just one rolled up column:

.. csv-table::
   :header-rows: 1
   :file: ../examples/cafe/tables-human-2/data.csv

Here's what we get when we run this new data with this schema:

.. literalinclude:: ../examples/cafe/tables-human-2/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/tables-human-2/expected.json
   :language: json


Relationships using Identifiers
===============================

So far, all the examples you've seen have served to demonstrate how Flatten
Tool works, but probably wouldn't be particularly useful in real life, simply
because they require everything related to be on the same row.

In this section you'll learn how identifiers work and that will allow you much
more freedom in designing different spreadsheet layouts that produce the same
JSON.

In Flatten Tool, any field named ``id`` is considered special. Flatten Tool knows
that any objects with the same ``id`` at the same level are the same object and
that their values should be merged.


ID-based object merge behaviour
-------------------------------

The merge behaviour happens whether the two IDs are specified in:

* different rows in the same sheet
* two rows in two different sheets

Basically, any time Flatten Tool comes across a row with an ``id`` in it, it will
lookup any other objects in the array to see if that ``id`` is already used and if
it is, it will merge it. If not, it will just append a new object to the array.

.. caution::

   It is important to make sure your ``id`` values really are unique. If you
   accidentally use the same ``id`` for two different objects, Flatten Tool
   will think they are the same and merge them.


Flatten Tool will merge an existing and new object as follows:

* Any fields in new object that are missing in the existing one are added

* Any fields in the existing object that aren't in the new one are left as
  they are

* If there are fields that are in both that have the same value, that value
  is kept

* If there are fields that are in both with different values, the existing
  values are kept and conflict warnings issued

This means that values in later rows do not overwrite existing conflicting
values.

Let's have a look at these rules in action in the next two sections with an
example from a single sheet, and one from multiple sheets.


ID-based object merge in a single sheet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's an example that demonstrates these rules:

.. csv-table::
   :file: ../examples/cafe/relationship-merge-single/data.csv
   :header-rows: 1

Let's run it:

.. literalinclude:: ../examples/cafe/relationship-merge-single/cmd.txt
   :language: bash

Notice the warnings above about values being over-written:

.. literalinclude:: ../examples/cafe/relationship-merge-single/expected_stderr.json

The actual JSON contains a single Cafe with ``id`` value ``CAFE-HEALTH`` and all
the values merged in:

.. literalinclude:: ../examples/cafe/relationship-merge-single/expected.json
   :language: json


ID-based object merge in multiple sheets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's an example that uses the same data as the single sheet example above,
but spreads the rows over four sheets named ``a``, ``b``, ``c`` and ``d``:

.. csv-table:: sheet: a
   :file: ../examples/cafe/relationship-merge-multiple/a.csv
   :header-rows: 1

.. csv-table:: sheet: b
   :file: ../examples/cafe/relationship-merge-multiple/b.csv
   :header-rows: 1

.. csv-table:: sheet: c
   :file: ../examples/cafe/relationship-merge-multiple/c.csv
   :header-rows: 1

.. csv-table:: sheet: d
   :file: ../examples/cafe/relationship-merge-multiple/d.csv
   :header-rows: 1

Let's run it:

.. literalinclude:: ../examples/cafe/relationship-merge-multiple/cmd.txt
   :language: bash

Notice the warnings above about values being over-written:

.. literalinclude:: ../examples/cafe/relationship-merge-multiple/expected_stderr.json

And the rest of the output:

.. literalinclude:: ../examples/cafe/relationship-merge-multiple/expected.json
   :language: json

The result is the same as before.


Parent-child relationships (arrays of objects)
----------------------------------------------

Things get much more interesting when you start dealing with arrays of objects
whose parents have an ``id``. This enables you to split the parents and children
up into multiple sheets rather than requiring everything sits one the same row.

As an example, let's imagine that ``Vegetarian Cafe`` is arranged having two
tables numbered ``16`` and ``17`` because they are share tables with another
restaurant next door.

.. literalinclude:: ../examples/cafe/relationship-lists-of-objects-simple/expected.json
   :language: json

From the knowledge you gained when learning about arrays of objects without IDs
earlier, you know that you can produce the correct structure with a CSV file
like this:

.. csv-table:: sheet: cafes
   :file: ../examples/cafe/relationship-lists-of-objects-simple/data.csv
   :header-rows: 1

This time, we'll give both the Cafe's IDs and move the tables into a separate
sheet:

.. csv-table:: sheet: cafes
   :file: ../examples/cafe/relationship-lists-of-objects/cafes.csv
   :header-rows: 1

.. csv-table:: sheet: tables
   :file: ../examples/cafe/relationship-lists-of-objects/tables.csv
   :header-rows: 1

By having the tables in a separate sheet, you can now support cafe's with as
many tables as you like, just by adding more rows and making sure the ``id``
column for the table matches the ``id`` value for the cafe.

Let's run this example:

.. literalinclude:: ../examples/cafe/relationship-lists-of-objects/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/relationship-lists-of-objects/expected.json
   :language: json

By specifying an ID, the values in the tables sheet can be associated with the
correct part of the tree created by the cafes sheet.


Index behaviour
---------------

Within the array of tables for each cafe, you might have noticed that each table
number has a JSON Pointer that ends in with ``/0/number``. Since they all have the
same index, they are simply ordered within each cafe in the order of the rows
in the sheet.


Grandchild relationships
------------------------

In future we might like to extend this example so that we can track the dishes
ordered by each table so we can generate a bill.

Let's take the case of dishes served at tables and imagine that ``Healthy Cafe``
has its own health ``fish and chips`` dish. Now let's also imagine that the dish
is ordered at tables 1 and 3.

If you are used to thinking about relational database you would probably think
about having a new sheet called ``dishes`` with a two columns, one for an ``id``
and one for the ``name`` of the dish. You would then create a sheet to represent
a join table called ``table_dishes`` that contained the ID of the table and of
the dish.

The problem with this approach is that the output is actually a tree, and not a
normalised relational model. Have a think about how you would write the
``table_dishes`` sheet. You'd need to write something like this:

.. csv-table::
   :header-rows: 1

    table/0/id,dish/0/id
    TABLE-1,DISH-fish-and-chips
    TABLE-3,DISH-fish-and-chips

The problem is that ``dish/0/id`` is really a JSON Pointer to ``/cafe/0/dish/0/id``
and so would try to create a new ``dish`` key under each *cafe*, not a ``dish`` key
under each *table*.

You can't do it this way. Instead you have to design you ``dish`` sheet to
specify both the ID of the cafe and the ID of the table as well as the name of
the dish. If a dish is used in multiple tables, you will have multiple rows,
each with the same name in the name column. In this each way row contains the
entire path to its position in the tree.

Since nothing depends on the dishes yet, they don't have to have an ID
themselves, they just need to reference their parent IDs:

.. csv-table:: sheet: cafes
   :file: ../examples/cafe/relationship-multiple/cafes.csv
   :header-rows: 1

.. csv-table:: sheet: tables
   :file: ../examples/cafe/relationship-multiple/tables.csv
   :header-rows: 1

.. csv-table:: sheet: dishes
   :file: ../examples/cafe/relationship-multiple/dishes.csv
   :header-rows: 1

Here are the results:

.. literalinclude:: ../examples/cafe/relationship-multiple/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/relationship-multiple/expected.json
   :language: json

Notice the ordering in this example. Because ``dishes`` is processed before
``tables``, ``TABLE-3`` gets defined before ``TABLE-2``, and ``dish`` gets added as a
key before ``tables``.

If the sheets were processed the other way around the data would be the same,
but the ordering different.

.. tip::

   Flatten Tool supports producing JSON hierarchies of arbitrary depth, not just
   the parent-child and parent-child-grandchild relationships you've seen in the
   examples so far. Just make sure that however deep an object is, it always has
   the IDs of *all* of its parents in the same row as it, as the tables and dishes
   sheets do.


Arbitrary-depth in a single table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also structure all the data into a single table. It is only
recommended to do this if you have a very simple data structure where there is
only one object at each part of the hierarchy.

In this example we'll use a JSON Schema to infer the structure, allowing us to
use human-readable column titles.

Here's the data:

.. csv-table:: sheet: dishes
   :file: ../examples/cafe/relationship-grandchild/cafes.csv
   :header-rows: 1

Let's unflatten this table:

.. literalinclude:: ../examples/cafe/relationship-grandchild/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/relationship-grandchild/expected.json
   :language: json

If you'd like to explore this example yourself, here's the schema used in the
example above:

.. literalinclude:: ../examples/receipt/cafe.schema
   :language: json


Missing IDs
-----------

You might be wondering what happens if IDs are accidentally missing. There are
two cases where this can happen:

* The ID is missing but no child objects reference it anyway
* The ID is missing and so children can't be added

To demonstrate both of these in one example consider the following example. In particular notice that:

* ``CAFE-VEG`` is missing from the ``cafes`` sheet
* ``CAFE-VEG`` is missing from the last row in the ``tables`` sheet

.. csv-table:: sheet: cafes
   :file: ../examples/cafe/relationship-missing-ids/cafes.csv
   :header-rows: 1

.. csv-table:: sheet: tables
   :file: ../examples/cafe/relationship-missing-ids/tables.csv
   :header-rows: 1

Let's run this example:

.. literalinclude:: ../examples/cafe/relationship-missing-ids/cmd.txt
   :language: bash
.. literalinclude:: ../examples/cafe/relationship-missing-ids/expected.json
   :language: json

You'll notice that all the data and tables for ``CAFE-HEALTH`` are output
correctly in the first object. This is what we'd expect because all the IDs
were present.

.. code-block:: text

        {
            "id": "CAFE-HEALTH",
            "name": "Healthy Cafe",
            "address": "123 City Street, London",
            "table": [
                {
                    "number": "1"
                },
                {
                    "number": "2"
                },
                {
                    "number": "3"
                }
            ]
        },

Next is this cafe:

.. code-block:: text

        {
            "name": "Vegetarian Cafe",
            "address": "42 Town Road, Bristol"
        },

This is as much information as Flatten Tool can work out from the second row of
the ``cafes`` sheet because the ID is missing. Flatten Tool just appends a new
cafe with the data it has.

Next, Flatten Tool works through the ``tables`` sheet, it finds table 16 and
knows it must be associated with a cafe called ``CAFE-VEG`` that is specified in
the ``id`` column, but because this ``id`` is present in the ``cafes`` sheet, it
can't merge it in. Instead it just appends data for the cafe:

.. code-block:: text

        {
            "id": "CAFE-VEG",
            "table": [
                {
                    "number": "16"
                }
            ]
        },

Finally, Flatten Tool finds table 17 in the ``tables`` sheet. It doesn't know
which Cafe this is for, but it knows tables are part of cafes so it adds
another unnamed cafe:

.. code-block:: text

        {
            "table": [
                {
                    "number": "17"
                }
            ]
        }


Relationships with JSON Schema
------------------------------

If you want to use Flatten Tool's support for JSON Schema to extend to relationships
you need to amend your JSON Schema to tell it about the ``id`` fields:

#. Make sure that the ``id`` field is specified for every object in the hierarchy
   (although this isn't necessary for objects right at the bottom of the hierarchy)

#. Give the ``id`` field a title of ``Identifier``

With these two things in place, Flatten Tool will correctly handle relationships.

.. caution::

   If you forget to add the ``id`` field, Flatten Tool will not know anything
   about it when generating templates or converting titles.


Sheet Shapes
============

Now that you've seen some of the details of how Flatten Tool works we can look
in more detail at the different shapes your data can have in the sheets.

To discuss the pros and cons of the different shapes, we'll work through a whole
example.

Imagine that you Healthy Cafe and Vegetarian Cafe are both part of a chain and
you have to create a receipt system for them. You need to track which dishes
are ordered at which tables in which cafes.

The JSON you would like to produce from the sheets the waiters write as they
take orders looks like this:

.. literalinclude:: ../examples/receipt/normalised/expected.json
   :language: json

There are many ways we could arrange this data:

* cafes, tables and dishes all separate

* cafes and tables together, dishes separate, with one row per table in the cafes and tables sheet

* cafes and tables together, dishes separate, with one row per cafe in the cafes and tables sheet

* tables and dishes together, cafes separate, with one row per table in the tables and dishes sheet

* tables and dishes together, cafes separate, with one row per dish in the tables and dishes sheet

Let's take a look at the first three cases. Combining tables and dishes into
one sheet follows the same principles as combining cafes and tables, so we
won't demonstrate those examples too.


Separate sheet for each object
------------------------------

Here's the first way of doing this with everything in its own sheet. This is
the recommended approach unless you have a good reason to move some parts of a
table into another one. It is also the default you will get when using Flatten
Tool to flatten or generate a template for a JSON structure. You'll learn about
that later.

.. csv-table:: Sheet: 1_cafes
   :file: ../examples/receipt/normalised/1_cafes.csv
   :header-rows: 1

.. csv-table:: Sheet: 2_tables
   :file: ../examples/receipt/normalised/2_tables.csv
   :header-rows: 1

.. csv-table:: Sheet: 3_dishes
   :file: ../examples/receipt/normalised/3_dishes.csv
   :header-rows: 1

.. note ::

   Notice that this time the CSV sheets are prefixed with an integer to make
   sure they are processed in the right order. If the prefixes weren't there,
   the order of the tables in the resulting JSON might be different.

   If you were using an XLSX file, Flatten Tool would process the sheets in
   the order they appeared, regardless of their names, so the prefix
   wouldn't be needed.

You can run the example with this:

.. literalinclude:: ../examples/receipt/normalised/cmd.txt
   :language: bash

You should see the same JSON as shown at the top of the section.

The advantage of this set up is that it allows any number of cafes, tables and
dishes. The disadvantage is that it requires three sheets, making data a bit
harder to find.


Combining objects
-----------------

Now let's imagine that all your cafe's are small and they never have more than
three tables. In this case we can combine tables into cafes so that we just
have two sheets.


Table per row
~~~~~~~~~~~~~

Here's what it looks like when you want to use one row per table:

.. csv-table:: Sheet: cafes and tables
   :file: ../examples/receipt/combine-table-into-cafe/cafes_and_tables.csv
   :header-rows: 1

.. csv-table:: Sheet: dishes
   :file: ../examples/receipt/combine-table-into-cafe/dishes.csv
   :header-rows: 1

You can run the example with this:

.. literalinclude:: ../examples/receipt/combine-table-into-cafe/cmd.txt
   :language: bash

If you do run it you'll see the JSON is exactly the same as before.

Unlike a database, Flatten Tool won't complain if different Cafe names are
associated with the same Cafe ID in the same table, instead you'll just get a
warning.

Combining sheets works best when:

* the child (the object being combined in to the parent) doesn't have that many properties
* you can be sure there won't be too many children for each parent
* there is a low risk of typos being made in the duplicated data


Cafe per row
~~~~~~~~~~~~

There's another variant of this shape that we can use. If we just want to use
one row per cafe.

.. csv-table:: Sheet: cafes and tables
   :file: ../examples/receipt/combine-table-into-cafe-2/cafes_and_tables.csv
   :header-rows: 1

.. csv-table:: Sheet: dishes
   :file: ../examples/receipt/combine-table-into-cafe-2/dishes.csv
   :header-rows: 1

You can run the example with this:

.. literalinclude:: ../examples/receipt/combine-table-into-cafe-2/cmd.txt
   :language: bash

The JSON is the same as before, as you would expect.


All in one table
~~~~~~~~~~~~~~~~

It would also be possible to put all the data in a single table, but this would
look quite complicated since there is more than one table in each cafe and more
than one dish at each table.

To understand the approach, have a look at the "Arbitrary-depth in a single
table" section earlier.

.. tip ::

   If you'd like to explore these examples yourself using human-readable column
   titles, you can use the schema in the "Arbitrary-depth in a single
   table" section too.

Metadata Tab
============

Flatten Tool supports naming of a special sheet (or Tab) in a spreadsheet to add data to the top level of the returned data structure.  Currently it only supports output format JSON and the input format has to be XLSX.

Example Usage
-------------

You have a spreadsheet named "mydata.xlsx with" 2 sheets. The first sheet named "Cafe":

.. csv-table::
   :header-rows: 1
   :file: ../examples/cafe/meta-tab/data.csv

A second sheet you would like to add some metadata to this list of rows to a sheet named "Meta":

.. csv-table::
   :file: ../examples/cafe/meta-tab/metadata.csv

As you can see it is also possible to choose to have the metadata headings on the first column (not the first row) with metadata vertical.

The command for doing this:

.. literalinclude:: ../examples/cafe/meta-tab/cmd.txt
   :language: bash

.. literalinclude:: ../examples/cafe/meta-tab/expected.json
   :language: json

Options
-------

``--metatab-name``

This is the name of the sheet with the metadata on. It is case sensitive. It is the only mandatory option if you want to parse a metatab, without it no metatab will be parsed

``--metatab-schema``

The JSON schema of the metatab. This schema will be used to determine the types and/or titles of the data in the metatab.  It works in the same way as the --schema option but just for the metatab.  The schema used with the --schema option has no effect on the metatab parsing, so this has to be specified if you need title handling or want to specify types.

``--metatab-only``

Just return the metatab information and not the rest of the doc. Using the example above:

.. literalinclude:: ../examples/cafe/meta-tab-only/cmd.txt
   :language: bash

.. literalinclude:: ../examples/cafe/meta-tab-only/expected.json
   :language: json

``--metatab-vertical-orientation``

Say that the metatab data runs vertically rather that horizontally see example above.

Configuration properties: skip and header rows
==============================================

Flatten Tool supports directives in the first row of a file to tell it to:

* **skiprows** - start processing data from n rows down
* **headerrows** - the total number of header rows. Note that the first header row will be treated as field paths.

Example usage
-------------

You have a CSV file named "mydata.csv" that contains:

* Two rows of general provenance information or notes;
* The field paths;
* Two rows that explain the meaning of the fields

This pattern may occur, for example, when you export from a spreadsheet that includes formatted header rows that explain the data.

By adding a row containing a cell with '#', and then a set of configuration directives, you can instruct Flatten Tool to skip rows at the top of the file, and to recognise that the field paths are followed by a set of additional header lines. 

.. csv-table::
   :file: ../examples/cafe/skip-and-headers/data.csv

Flatten tool will interpret the '#' configuration row, and generate the appropriate output with no additional parameters needed at the command line.

.. literalinclude:: ../examples/cafe/skip-and-headers/cmd.txt
   :language: bash

.. literalinclude:: ../examples/cafe/skip-and-headers/expected.json
   :language: json

List of configuration features
------------------------------

There is also the 'ignore' command, which can be used to ignore sheets in a multi-tab workbook. 

When configuration options are set in metatab, they apply to all sheets unless they are overridden. 

Further configuration options can be seen at https://github.com/OpenDataServices/flatten-tool/blob/7fa96933b8fc3ba07a3d44fe07dccf2791165686/flattentool/lib.py 


Source maps
===========

Once you have unflattened a spreadsheet into a JSON document you will usually
pass the document to a JSON Schema validator to make sure all the data is
valid.

If there are any errors in the JSON, it is very useful to be able to point the
user back to the corresponding place in the original spreadsheet. Flatten Tool
provides *source maps* for exactly this purpose.

There are two types of source map:

* Cell source map - points from a JSON pointer path to a cell (or row) in the
  original spreadsheet
* Heading source map - specifies the column for each heading

Here's an example where we unflatten a normalised spreadsheet, but generate
both a cell and a heading source map as we do.

.. literalinclude:: ../examples/receipt/source-map/cmd.txt
   :language: bash

Here's the source data:

.. csv-table:: sheet: 1_cafes.csv
   :file: ../examples/receipt/source-map/input/1_cafes.csv
   :header-rows: 1

.. csv-table:: sheet: 2_tables.csv
   :file: ../examples/receipt/source-map/input/2_tables.csv
   :header-rows: 1

.. csv-table:: sheet: 3_dishes.csv
   :file: ../examples/receipt/source-map/input/3_dishes.csv
   :header-rows: 1

Here's the resulting JSON document (the same as before):

.. literalinclude:: ../examples/receipt/source-map/expected.json
   :language: json

Let's look in detail at the cell source map and heading source map for this example.

Cell source map
---------------

A cell source map maps each JSON pointer in the document above back to the
cells where that value is referenced.

Using the example you've just seen, let's look at the very last value in the
spreadsheet for the number of ``TABLE-17`` in ``CAFE-VEG``. The JSON pointer is
``cafe/1/table/1/number`` and the value itself is ``17``.

Looking back at the source sheets you can see the only place this value appears
is in ``2_tables.csv``. It appears in column C (the third column), row 6 (row 1
is treated as the heading so the values start at row 2). The heading of this
column in ``table/0/number`` (which happens to be a JSON pointer, but if we were
using human readable headings, those headings would be used instead). We'd
therefore expect the cell source map to have just one entry for
``cafe/1/table/1/number`` that points to cell ``C2`` like this:

::

    "cafe/1/table/1/number": [
        [
            "2_tables",
            "C",
            6,
            "table/0/number"
        ]
    ],

Here's the actual cell source map and as you can see, the entry for
``cafe/1/table/1/number`` is as we expect (it is near the end):

.. literalinclude:: ../examples/receipt/source-map/expected/cell_source_map.json
   :language: json

You'll notice that some JSON pointers map to multiple source cells. This
happens when data appears in multiple places, such as when the cell refers to
an identifier.

You'll also notice that after all the JSON pointers that point to values such
as ``cafe/0/id`` or ``cafe/1/table/1/number`` there are a set of JSON pointers that
point to objects rather than cells. For example ``cafe/0`` or ``cafe/1/table/1``.
These JSON pointers refer back to the rows which contain values that make up
the object. For example ``cafe/1/table/1`` looks like this:

::

    "cafe/1/table/1": [
        [
            "2_tables",
            6
        ]
    ]

This tells us that the data that makes up that table in the final JSON was all
defined in the ``2_tables`` sheet, row 6 (remembering that rows start at 2
because the header row is row 1). Again, if data from multiple rows goes to
make up the object, there may be multiple arrays in the JSON pointer result.

This second kind of entry in the cell source map is useful when a JSON schema
validator gives errors to describe a missing value since it is likely that
you will need to add the value on one for the rows where the other values are
defined.

Heading source map
------------------

The heading source map maps a JSON pointer with all numbers removed, back to
the column heading at the top of the columns where corresponding values have
been placed.

Here's the heading source map that was generated in the example we've been
using in this section:

.. literalinclude:: ../examples/receipt/source-map/expected/heading_source_map.json
   :language: json

The heading source map is generated separately from the cell source map, so
headings can be found even if they have no corresponding data in the resulting
JSON.
