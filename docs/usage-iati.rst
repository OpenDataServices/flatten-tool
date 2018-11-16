Flatten Tool for IATI
=====================

Currently flatten-tool only supports Spreadsheet->XML for IATI (unflatten), not conversion in the other direction, or automated template creation.

Convert a spreadsheet to XML
----------------------------

For an XLSX file called ``filename.xlsx``:

.. code-block:: bash

    flatten-tool unflatten --xml --id-name iati-identifier --root-list-path iati-activity -o iati.xml -f xlsx filename.xlsx 


For a directory of CSV files called ``csv_directory``:

.. code-block:: bash

    flatten-tool unflatten --xml --id-name iati-identifier --root-list-path iati-activity -o iati.xml -f csv csv_directory

(Outputs a file called ``iati.xml``).


Example
-------

Given these two sheets:

.. csv-table:: sheet: main.csv
   :file: ../examples/iati/main.csv

.. csv-table:: sheet: transactions.csv
   :file: ../examples/iati/transactions.csv

Running this command:

.. literalinclude:: ../examples/iati/cmd.txt
   :language: bash

Produces this XML:

.. literalinclude:: ../examples/iati/expected.xml
   :language: xml
