Flatten Tool for 360Giving
==========================

You can also upload the file to http://cove.opendataservices.coop/360

Download
https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json
to the current directory.

.. code-block:: bash

    flatten-tool create-template --output-format all --output-name 360giving-template --schema 360-giving-schema.json --main-sheet-name grants --rollup --use-titles

.. code-block:: bash

    flatten-tool unflatten -o out.json -f xlsx input.xlsx --schema 360-giving-schema.json --convert-titles --root-list-path='grants'


