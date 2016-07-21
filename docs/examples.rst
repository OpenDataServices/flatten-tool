Examples
========

Simple example
--------------

The JSON :download:`simple.json <../examples/simple.json>`:

.. literalinclude:: ../examples/simple.json
   :language: json

Can be converted to/from a spreadsheet like :download:`simple/main.csv <../examples/simple/main.csv>`:

.. csv-table::
   :file: ../examples/simple/main.csv
   :header-rows: 1

Using the commands:

.. code-block:: bash

    flatten-tool unflatten -f csv examples/simple -o examples/simple.json
    flatten-tool flatten -f csv examples/simple.json -o examples/simple


One to many relationships (JSON arrays)
---------------------------------------

There are multiple shapes of spreadsheet that can be used to produce the same JSON arrays. E.g. to produce :download:`this JSON <../examples/array_multisheet.json>`:

.. literalinclude:: ../examples/array_multisheet.json
   :language: json

We can use these Spreadsheets:

.. csv-table::
   :file: ../examples/array_multisheet/a.csv
   :header-rows: 1

.. csv-table::
   :file: ../examples/array_multisheet/main.csv
   :header-rows: 1

These are also the spreadsheets that flatten-tool's `flatten` (JSON to Spreadsheet) will produce.

Commands used to generate this:

.. code-block:: bash

    flatten-tool unflatten -f csv examples/array_multisheet -o examples/array_multisheet.json
    flatten-tool flatten -f csv examples/array.json -o examples/array_multisheet

However, there are other "shapes" of spreadsheet that can produce the same JSON.

New columns for each item of the array:

.. csv-table::
   :file: ../examples/array_pointer/main.csv
   :header-rows: 1

.. code-block:: bash

    flatten-tool unflatten -f csv examples/array_pointer -o examples/array.json

Repeated rows:


.. csv-table::
   :file: ../examples/array_repeat_rows/main.csv
   :header-rows: 1

.. code-block:: bash
    
    flatten-tool unflatten -f csv examples/array_repeat_rows -o examples/array.json


Arrays within arrays
--------------------

.. literalinclude:: ../examples/double_array.json
   :language: json

.. csv-table::
   :file: ../examples/double_array_multisheet/a.csv
   :header-rows: 1

.. csv-table::
   :file: ../examples/double_array_multisheet/main.csv
   :header-rows: 1

