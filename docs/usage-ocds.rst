Usage for OCDS
==============

You can also upload the file to http://standard.open-contracting.org/validator/

Creating spreadsheet templates
------------------------------

Download https://raw.githubusercontent.com/open-contracting/standard/1.0/standard/schema/release-schema.json to the current directory.

.. code-block:: bash

    flatten-tool create-template --root-id=ocid --output-format all --output-name template --schema release-schema.json --main-sheet-name releases

This will create `template.xlsx` and a `template/` directory of csv files.

See `flatten-tool --help` for details of the commandline options.


Converting a populated spreadsheet to JSON
------------------------------------------

.. code-block:: bash

    cp base.json.example base.json

And populate this with the package information for your release.

Then, for a populated xlsx template in (in release_populated.xlsx):

.. code-block:: bash

    flatten-tool unflatten release_populated.xlsx --root-id=ocid --base-json base.json --input-format xlsx --output-name release.json --root-list-path='releases'

Or for populated CSV files (in the release_populated directory):

.. code-block:: bash

    flatten-tool unflatten release_populated --root-id=ocid --base-json base.json --input-format csv --output-name release.json --root-list-path='releases'

These produce a release.json file based on the data in the spreadsheets.


Converting a JSON file to a spreadsheet
---------------------------------------

.. code-block:: bash

    flatten-tool flatten input.json --root-id=ocid --main-sheet-name releases --output-name flattened --root-list-path='releases'

This will create `flattened.xlsx` and a `flattened/` directory of csv files.
