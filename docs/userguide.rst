Spreadsheet Designer's Guide
++++++++++++++++++++++++++++

Flatten Tool is a Python library and command line interface for converting
spreadsheets containing one or more sheets to a JSON tree structure and back
again. Flatten Tool can make use of a JSON Schema to help with this process.

In this guide you'll learn the various rules Flatten Tool uses to convert one
or more sheets in a spreadsheet into the JSON tree by looking at lots of
different examples based around Cafes. Once you've understood how Flatten Tool
works you should be able to design your own spreadsheet structures, debug
problems in your spreadsheets and be able to make use of Flatten Tool's more
advanced features.

Before we get into too much detail though, let's start by looking
at the Command Line API.

Command-Line API
================

To demonstrate the command line API you'll start with the simplest possible
example, a sheet listing Cafe names:

.. csv-table::
   :file: ../examples/cafe/simple/data.csv
   :header-rows: 1

We'd like Flatten Tool to convert it to the following JSON structure for a list
of cafes, with the name being the only information we want for each one:

.. code-block:: json

    {
        "cafe": [
            {
                "name": "Healthy Cafe"
            }
        ]
    }

Let's try converting the sheet to the JSON above.

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/simple
    {
        "main": [
            {
                "name": "Healthy Cafe"
            }
        ]
    }

That's not too far off what we wanted. You can see the data structure we
expected, but Flatten Tool has guessed that each row in the spreadsheet
represents something that should be under a `main` key. That isn't quite right,
so let's tell it that the rows are cafes and should come under a `cafe` key.
You do that with a *root list path*.


Root List Path
--------------

The *root list path* is the key which Flatten Tool should add a list of objects
representing each row to. You can specify it with the `--root-list-path`
option. If you don't specify it, `main` is used as the default as you saw in
the last example.

Let's set `--root-list-path` to `cafe` so that our original input generates the
JSON we were expecting:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/simple --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe"
            }
        ]
    }

That's what we expected. Great.

.. note ::

    Although `--root-list-path` sounds like it accepts a path such as
    `building/cafe`, it only accepts a single key.

Writing output to a file
------------------------

By default, Flatten Tool now prints its output to stdout. If you want it to instead write its output to a file you can use the `-o` option.

Here's the same example, this time writing its output to `unflattened.json`:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/simple --root-list-path 'cafe' -o unflattened.json

Let's `cat` the output to check it is the same:

.. code-block:: bash

    $ cat unflattened.json
    {
        "cafe": [
            {
                "name": "Healthy Cafe"
            }
        ]
    }


Base JSON
---------

If you want the resulting JSON to also include other keys that you know in
advance, you can specify them as `base.json` and Flatten Tool will merge its
data into that file.

For example, if `base.json` looks like this:

.. literalinclude:: ../examples/cafe/one-cafe/base.json
   :language: json

and the data looks like this:

.. csv-table::
   :file: ../examples/cafe/one-cafe/data.csv
   :header-rows: 1

When you run this command on the same CSV file and using the `--base-json` flag
too, you'll see this, with the spreadsheet rows merged in:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/one-cafe --root-list-path='cafe' --base-json=examples/cafe/one-cafe/base.json
    {
        "country": "England",
        "cafe": [
            {
                "name": "Healthy Cafe"
            }
        ]
    }

.. caution ::

   If you give the base JSON the same key as you specify in `--root-list-path`
   then Flatten Tool will overwrite its value.


Understanding JSON Pointer and how Flatten Tool uses it
=======================================================

Let's consider our first example again:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/simple --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe"
            }
        ]
    }

Although so far we've been using a very simple example, it is worth
understanding a little about the algorithm being applied behind the scenes.

The key to understanding how Flatten Tool represents more complex examples in a
spreadsheet lies in knowing about the `JSON Pointer specification
<https://tools.ietf.org/html/rfc6901>`_.  This specification describes a way to
reference values in a JSON document. For example `/cafe/0/name` would point to
value `Healthy Cafe` in the JSON Document above

.. note ::

   JSON pointer starts array indexes at 0, hence the first cafe is at index 0.

Flatten Tool uses JSON Pointer as a way of describing how to move values out of
a spreadsheet and into a JSON document.

You can think of Flatten Tool doing the following as it parses a sheet:

* Load the base JSON or use an empty JSON object

* For each row:

   * Convert each column heading to a JSON pointer by removing whitespace and
     prepending with `/cafe/`, then adding the row index and another `/` to the
     front

   * Take the value in each column and associate it with the JSON pointer
     (treating any numbers as array indexes, and overwriting existing JSON pointer
     values for that row if necessary)

   * Write the value into the position in the JSON object being specified by the
     JSON pointer, creating more structures as you go

In this example there is only one sheet, and only one row, so when parsing that
first row, `/cafe/0/` is appended to `name` to give the JSON pointer
`/cafe/0/name`. Flatten Tool then writes `Health Cafe` in the correct position.

Multiple rows
-------------

Let's look at a multi-row example:

.. csv-table::
   :file: ../examples/cafe/simple-row/data.csv
   :header-rows: 1

This time `Healthy Cafe` would be placed at `/cafe/0/name` and `Vegetarian
Cafe` at `/cafe/1/name` producing this:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/simple-row --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe"
            },
            {
                "name": "Vegetarian Cafe"
            }
        ]
    }

Multiple columns
----------------

Let's add the cafe address to the spreadsheet:

.. csv-table::
   :header-rows: 1
   :file: ../examples/cafe/simple-col/data.csv


.. note ::

   CSV files require cells containing `,` characters to be escaped by wrapping
   them in double quotes. That's why if you look at the source CSV, the addresses
   are escaped with `"` characters.

This time `Healthy Cafe` is placed at `/cafe/0/name` as before, `London` is
placed at `/cafe/0/address`. `Vegetarian Cafe` at `/cafe/1/name` as before and
`Bristol` is at `/cafe/1/address`.

The result is:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/simple-col --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "address": "123 City Street, London"
            },
            {
                "name": "Vegetarian Cafe",
                "address": "42 Town Road, Bristol"
            }
        ]
    }

Multiple sheets
---------------

So far, all the examples have just used one sheet. When multiple sheets are
involved, the behaviour isn't much different. In effect, all Flatten Tool does
is take the JSON structure produced after processing the first sheet, and use
it as the base JSON for processing the next sheet.

Once all the sheets have been processed the resulting JSON is returned.

.. note ::

   The CSV specification doesn't support multiple sheets. To work around this,
   Flatten Tool treats a directory of CSV files as a single spreadsheet with
   multiple sheets - one for each file.

   This is why all the CSV file examples given so far have been written to a
   file in an empty directory and why only the directory name was needed in
   the `flatten-tool` commands.

Here's a simple two-sheet example where the headings are the same in both
sheets:

.. csv-table:: sheet: data
   :file: ../examples/cafe/multiple/data.csv
   :header-rows: 1


.. csv-table:: sheet: other
   :file: ../examples/cafe/multiple/other.csv
   :header-rows: 1


When you run the example you get this:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/multiple --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe"
            },
            {
                "name": "Vegetarian Cafe"
            }
        ]
    }

The order is because the `data` sheet was processed before the `other` sheet. The files are
processed in the order returned by `os.listdir()` so you should name them in
the order you would like them processed.

Index behaviour
~~~~~~~~~~~~~~~

If you think about what's going on in the previous example you might have
expected that `Vegetarian Cafe` would have over-written `Healthy Cafe` since
both are represented by the JSON pointer `/cafe/0/name`.

The reason this doesn't happen is that when there is a conflict in index
values, Flatten Tool simply appends the next item after the previous one with
that index. (Although as you'll see later in the relationships section, special
`id` values can alter this behaviour).

This behaviour has two advantages:

* data won't be lost if for some reason the index wasn't specified correctly

* the data in the generated JSON will be in the same order as it was specified
  in the sheets which is likely to be what the person putting data into the
  spreadsheet would expect

This behaviour is also important when you learn about Lists of Objects later.


Objects
=======

Now you know that the column headings are really just a JSON Pointer
specification, and the index values are only treated as indicators of the
presence of lists (and not their order) you can write some more sophisticated
examples.

Rather than have the address just as string, we could represent it as an
object. For example, imagine you'd like out output JSON in this structure:

.. code-block:: json

    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "address": {
                    "street": "123 City Street",
                    "city": "London"
                }
            },
            {
                "name": "Vegetarian Cafe",
                "address": {
                    "street": "42 Harbour Way",
                    "city": "Bristol"
                }
            }
        ]
    }

You can do this by knowing that the JSON Pointer to "123 City Street" would be
`/cafe/0/address/street` so that we would need to name the street column
`address/street`.

Here's the data:

.. csv-table::
   :file: ../examples/cafe/object/data.csv
   :header-rows: 1

Let's try it:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/object --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "address": {
                    "street": "123 City Street",
                    "city": "London"
                }
            },
            {
                "name": "Vegetarian Cafe",
                "address": {
                    "street": "42 Town Road",
                    "city": "Bristol"
                }
            }
        ]
    }



Lists of Objects
================

The cafe's that have made up our examples so far also have tables, and the
tables have a table number so that the waiters know where the food has to be
taken to.

Each cafe has many tables, so this is an example of a one-to-many relationship
if you are used to working with relational databases.

We can represent the table information in JSON as a list of objects, where each
object represents a table, and each table has a `number` key. Let's imagine the
`Healthy Cafe` has three tables numbered 1, 2 and 3. We'd like to produce this
structure:

.. code-block:: json

    {
        "cafe": [
            {
                "name": "Healthy Cafe"
                "table": [
                    {
                        "number": "1",
                    },
                    {
                        "number": "2",
                    },
                    {
                        "number": "3",
                    }
                ]
            }
        ]
    }


In the relationships section later, we'll see other ways of arranging this data
using *identifiers*, but for now we'll demonstrate an approach that puts all
the table information in the same row as the cafe itself. This is called
*Rolling up* data in Flatten Tool terminology.

For example, consider this spreadsheet data:

.. csv-table::
   :file: ../examples/cafe/one-table/data.csv
   :header-rows: 1


.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/tables --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
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
            }
        ]
    }

Index behaviour
---------------

Just as in the multiple sheets example earlier, the exact numbers at the table index
positions aren't too important to Flatten Tool. They just tell Flatten Tool
that the value in the cell is part of an object in a list.

In this particular case though, Flatten Tool will keep columns in order implied by the indexes.

For example here the index values are such that the lowest number comes last:

.. csv-table::
   :file: ../examples/cafe/tables-index/data.csv
   :header-rows: 1

We'd still expect 3 tables in the output, but we expect Flatten Tool to re-order the columns so that table 3 comes first, then 2, then 1:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/tables-index --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "table": [
                    {
                        "number": "3"
                    },
                    {
                        "number": "2"
                    },
                    {
                        "number": "1"
                    }
                ]
            }
        ]
    }

Child objects like these tables can, of course have more than one key. Let's
add a `reserved` key to table number 1 but to try to confuse Flatten Tool,
we'll specify it at the end:

.. csv-table::
   :file: ../examples/cafe/tables-index/data.csv
   :header-rows: 1

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/tables-index-reserved/ --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "table": [
                    {
                        "number": "3"
                    },
                    {
                        "number": "2"
                    },
                    {
                        "number": "1",
                        "reserved": "True"
                    }
                ]
            }
        ]
    }

Notice that Flatten Tool correctly associated the `reserved` key with table 1
because of the index numbered `30`, even though the columns weren't next to
each other.

For a much richer way of organising lists of objects, see the Relationships
section.

Plain Lists (Unsupported)
-------------------------

Flatten Tool doesn't support lists of JSON values other than objects (just
described in the previous section).

As a result heading names such as `tag/0` and `tag/1` would be ignored and an
empty list would be put into the JSON.

Here's some example data:

.. csv-table::
   :file: ../examples/cafe/plain-list/data.csv
   :header-rows: 1

And the result:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/plain-list --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "tag": []
            },
            {
                "name": "Vegetarian Cafe",
                "tag": []
            }
        ]
    }


Typed fields
============

In the table example above, the table numbers are produced as strings in the
JSON. The JSON Pointer specification doesn't provide any way of telling you
what type the value being pointed to is, so we can't get the information from
the column headings.

There are two places we can get it from though:

* The spreadsheet cell (if the underlying spreadsheet type supports it)
* An external JSON Schema describing the data

Using spreadsheet cell formatting
---------------------------------

CSV files only support string values, so the easiest way to get the example
above to use integers would be to use a spreadsheet format such xlsx that
supported integers and make sure the cell type was number. Flatten Tool would
pass the cell value through to the JSON as a number in that case. Make sure you
specify the correct format `-f xlsx` on the command line if you want to use an
xlsx file.

.. code-block:: bash

    $ flatten-tool unflatten -f xlsx examples/cafe/tables.xlsx --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "table": [
                    {
                        "number": 3
                    },
                    {
                        "number": 2
                    },
                    {
                        "number": 1
                    }
                ]
            }
        ]
    }


Using a JSON Schema with types
------------------------------

Here's an example of a JSON Schema that can provide the typing information:

.. literalinclude:: ../examples/cafe/tables/cafe.schema
   :language: json

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/tables --root-list-path 'cafe' --schema=examples/cafe/tables/cafe.schema
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "table": [
                    {
                        "number": 1
                    },
                    {
                        "number": 2
                    },
                    {
                        "number": 3
                    }
                ]
            }
        ]
    }


Human-friendly headings using a JSON Schema with titles
=======================================================

Let's take a closer look at the last example again:

.. csv-table::
   :file: ../examples/cafe/tables/data.csv
   :header-rows: 1

The column headings `table/0/number`, `table/1/number` and `table/2/number` aren't very human readable, wouldn't it be great if we could use headings like this:

.. csv-table::
   :file: ../examples/cafe/tables-human-1/data.csv
   :header-rows: 1

Flatten Tool supports this if you do the following:

* Write a JSON Schema specifying the titles being used and specify it with the `--schema` flag
* Use `:` characters instead of `/` characters in the headings
* Specify the `--convert-titles` flag on the command line

.. caution::

   If you forget any of these, Flatten Tool might produce incorrect JSON rather than failing.

Here's a new JSON schema for this example:

.. literalinclude:: ../examples/cafe/tables-human-1/cafe.schema
   :language: json


Notice that both `Table` and `Number` are specified as titles.

Here's what we get when we run it:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/tables-human-1 --convert-titles --schema=examples/cafe/tables-human-1/cafe.schema --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "table": [
                    {
                        "number": 1
                    },
                    {
                        "number": 2
                    },
                    {
                        "number": 3
                    }
                ]
            }
        ]
    }


Optional array indexes
----------------------

Looking at the JSON Schema from the last example again you'll see that `table` is specified as an array type:

.. literalinclude:: ../examples/cafe/tables-human-1/cafe.schema
   :language: json

This means that Flatten Tool can work out that
any names specified in that column are part of that array. If you had an example with just one column representing each level of the tree, you could miss out the index in the heading when using `--convert-titles`.

Here's some example data:

.. csv-table::
   :header-rows: 1
   :file: ../examples/cafe/tables-human-2/data.csv

Here's what we get when we run this new data with this schema:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/tables-human-2 --convert-titles --schema=examples/cafe/tables-human-1/cafe.schema --root-list-path 'cafe'
    {
        "cafe": [
            {
                "name": "Healthy Cafe",
                "table": [
                    {
                        "number": 1
                    }
                ]
            }
        ]
    }

Relationships using Identifiers
===============================

So far, all the examples you've seen have served to demonstrate how Flatten
Tool works, but probably wouldn't be particularly useful in real life, simply
because they require everything related to be on the same row.

In this section you'll learn how identifiers work and that will allow you much
more freedom in designing different spreadsheet layouts that produce the same
JSON.

In Flatten Tool, any field named `id` is considered special. Flatten Tool knows
that any objects with the same `id` at the same level are the same object and
that their values should be merged.

The merge behaviour happens whether the two IDs are specified in:

* different rows in the same sheet
* two rows in two different sheets

Basically, any time Flatten Tool comes across a row with an `id` in it, it will
lookup any other objects in the list to see if that `id` is already used and if
it is, it will merge it. If not, it will just append a new object to the list.

.. caution ::

   It is important to make sure your `id` values really are unique. If you
   accidentally use the same `id` for two different objects, Flatten Tool
   will think they are the same and merge them.


Flatten Tool will merge objects as follows:

* Any fields that exist in the existing object, but not in the object being
  processed are kept as they are in the existing object

* Any fields that exist in the object being processed but, not in the existing
  object are kept as they are in the existing object being processed

* Any fields that existing on both are kept as they are in the existing object
  being processed, effectively overwriting what is there already and generating a
  warning

Single sheet
------------

Here's an example that demonstrates these rules:

.. csv-table::
   :file: ../examples/cafe/relationship-merge-single/data.csv
   :header-rows: 1

Let's run it and see what is generated:

.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/relationship-merge-single --root-list-path 'cafe'
    .../flattentool/input.py:114: UserWarning: Conflict when merging field "name" for id "CAFE-HEALTH" in sheet data: "Vegetarian Cafe" != "Health Cafe". If you were not expecting merging you may have a duplicate ID.
      key, id_info, debug_info.get('sheet_name'), base_value, value))
    .../flattentool/input.py:114: UserWarning: Conflict when merging field "number_of_tables" for id "CAFE-HEALTH" in sheet data: "3" != "4". If you were not expecting merging you may have a duplicate ID.
      key, id_info, debug_info.get('sheet_name'), base_value, value))

Notice the warnings above about values being over-written.

The actual JSON contains a single Cafe with `id` value `CAFE-HEALTH` and all the values merged in:

.. code-block:: json

    {
        "cafe": [
            {
                "id": "CAFE-HEALTH",
                "name": "Vegetarian Cafe",
                "number_of_tables": "3",
                "address": "123 City Street, London"
            }
        ]
    }


Multiple sheets
---------------

Here's an example that uses the same data as the single sheet example above, but spreads the rows over four sheets named `a`, `b`, `c` and `d`:


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


.. code-block:: bash

    $ flatten-tool unflatten -f csv examples/cafe/relationship-merge-multiple/ --root-list-path 'cafe'
    .../flattentool/input.py:114: UserWarning: Conflict when merging field "name" for id "CAFE-HEALTH" in sheet b: "Vegetarian Cafe" != "Health Cafe". If you were not expecting merging you may have a duplicate ID.
      key, id_info, debug_info.get('sheet_name'), base_value, value))
    .../flattentool/flattentool/input.py:114: UserWarning: Conflict when merging field "number_of_tables" for id "CAFE-HEALTH" in sheet d: "3" != "4". If you were not expecting merging you may have a duplicate ID.
      key, id_info, debug_info.get('sheet_name'), base_value, value))

And the rest of the output:

.. code-block:: json

    {
        "cafe": [
            {
                "id": "CAFE-HEALTH",
                "name": "Vegetarian Cafe",
                "number_of_tables": "3",
                "address": "123 City Street, London"
            }
        ]
    }

The result is the same as before.

Lists of Objects
----------------

Things get much more interesting when you start dealing with lists of objects whose parents have an `id`. This enables you to split the parents and children up into multiple sheets rather than requiring everything sits one the same row.

As an example, let's imagine that `Vegetarian Cafe` is arranged having two
tables numbered `16` and `17` because they are share tables with another
restaurant next door.

From the knowledge you gained when learning about lists of objects without IDs earlier, you know that you can produce the correct structure with a CSV file like this:

::

    name,table/0/number,table/1/number,table/2/number
    Healthy Cafe,1,2,3
    Vegetarian Cafe,16,17,

This time, we'll give both the Cafe's IDs and move the tables into a separate sheet:

.. csv-table:: sheet: cafes
   :file: ../examples/cafe/relationship-lists-of-objects/cafes.csv
   :header-rows: 1

.. csv-table:: sheet: tables
   :file: ../examples/cafe/relationship-lists-of-objects/tables.csv
   :header-rows: 1

By having the tables in a separate sheet, you can now support cafe's with as many tables as you like, just by adding more rows and making sure the `id` column for the table matches the `id` value for the cafe.

Let's run this example:

::

    $ flatten-tool unflatten -f csv examples/cafe/relationship-lists-of-objects --root-list-path 'cafe'
    {
        "cafe": [
            {
                "id": "CAFE-HEALTH",
                "name": "Healthy Cafe",
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
            {
                "id": "CAFE-VEG",
                "name": "Vegetarian Cafe",
                "table": [
                    {
                        "number": "16"
                    },
                    {
                        "number": "17"
                    }
                ]
            }
        ]
    }

By specifying an ID, the values in the tables sheet can be associated with the
correct part of the tree created by the cafes sheet.

Index behaviour
---------------

Within the list of tables for each cafe, you might have noticed that each table
number has a JSON Pointer that ends in with `/0/number`. Since they all have the
same index, they are simply ordered within each cafe in the order of the rows
in the sheet.

Multiple Relationships
----------------------

In future we might like to extend this example so that we can track the dishes
ordered by each table so we can generate a bill.

Let's take the case of dishes served at tables and imagine that `Healthy Cafe`
has its own health `fish and chips` dish. Now let's also imagine that the dish
is ordered at tables 1 and 3.

If you are used to thinking about relational database you would probably think
about having a new sheet called `dishes` with a two columns, one for an `id`
and one for the `name` of the dish. You would then create a sheet to represent
a join table called `table_dishes` that contained the ID of the table and of
the dish.

The problem with this approach is that the output is actually a tree, and not a
normalised relational model. Have a think about how you would write the
`table_dishes` sheet. You'd need to write something like this:

::

    table/0/id,dish/0/id
    TABLE-1,DISH-fish-and-chips
    TABLE-3,DISH-fish-and-chips

The problem is that `dish/0/id` is really a JSON Pointer to `/cafe/0/dish/0/id`
and so would try to create a new `dish` key under each *cafe*, not a `dish` key
under each *table*.

You can't do it this way. Instead you have to design you `dish` sheet to
specify both the ID of the cafe and the ID of the table as well as the name of
the dish. If a dish is used in multiple tables, you will have multiple rows,
each with the same name in the name column. In this each way row contains the
entire path to its position in the tree.

Since nothing depends on the dishes yet, they don't have to have an ID themselves, they just need to reference their parent IDs:

.. csv-table:: sheet: cafes
   :file: ../examples/cafe/relationship-multiple/cafes.csv
   :header-rows: 1

.. csv-table:: sheet: tables
   :file: ../examples/cafe/relationship-multiple/tables.csv
   :header-rows: 1

.. csv-table:: sheet: dishes
   :file: ../examples/cafe/relationship-multiple/dishes.csv
   :header-rows: 1

::

    $ flatten-tool unflatten -f csv examples/cafe/relationship-multiple --root-list-path 'cafe'
    {
        "cafe": [
            {
                "id": "CAFE-HEALTH",
                "name": "Healthy Cafe",
                "table": [
                    {
                        "id": "TABLE-1",
                        "dish": [
                            {
                                "name": "Fish and Chips"
                            }
                        ],
                        "number": "1"
                    },
                    {
                        "id": "TABLE-3",
                        "dish": [
                            {
                                "name": "Fish and Chips"
                            }
                        ],
                        "number": "3"
                    },
                    {
                        "id": "TABLE-2",
                        "number": "2"
                    }
                ]
            }
        ]
    }

Notice the ordering in this example. Because `dishes` is processed before
`tables`, `TABLE-3` gets defined before `TABLE-2`, and `dish` gets added as a
key before `tables`.

If the sheets were processed the other way around the data would be the same,
but the ordering different.

Receipt System Example
======================

Now that you've seen some of the details of how Flatten Tool works we can work
through a whole example.

Imagine that you Health Cafe and Vegetarian Cafe are both part of a chain and
you have to create a receipt system for them. You need to track which dishes
are ordered at which tables in which cafes.

The JSON you would like to produce from the sheets the waiters write as they
take orders looks like this:

XXX


There are three ways we could arrange this data.

XXX Re-write end-to-end tests with the cafe example here to demonstrate the
different shapes.
