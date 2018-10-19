Flatten Tool for OCDS
+++++++++++++++++++++

The `Open Contracting Data Standard (OCDS) <http://standard.open-contracting.org/>`__ has an `unofficial CSV serialization <http://standard.open-contracting.org/latest/en/implementation/serialization/#csv>`__ that can be converted to/from the canonical JSON form using Flatten Tool.

Templates
=========

Spreadsheet templates for OCDS can be downloaded from https://github.com/open-contracting/sample-data/tree/master/flat-template

These are generated with the commands listed in :ref:`ocds-cli-templates` below.

Web interface
=============

Flatten Tool is integrated into the `Open Contracting Data Standard Validator <http://standard.open-contracting.org/validator/>`__, an online tool for validating and converting OCDS files.

This supports XLSX, but currently only supports uploading CSV (and only one CSV file).

Command Line Usage
==================

Converting a JSON file to a spreadsheet
---------------------------------------

.. code-block:: bash

    flatten-tool flatten input.json --root-id=ocid --main-sheet-name releases --root-list-path=releases

This command will create an output called flattened in all the formats we support - currently this is ``flattened.xlsx`` and a ``flattened/`` directory of CSV files.

See ``flatten-tool flatten --help`` for details of the command line options.


Converting a populated spreadsheet to JSON
------------------------------------------

.. code-block:: bash

    cp base.json.example base.json

And populate this with the package information for your release.

Then, for a populated XLSX template (in release_populated.xlsx):

.. code-block:: bash

    flatten-tool unflatten release_populated.xlsx --root-id=ocid --base-json base.json --input-format xlsx --output-name release.json --root-list-path=releases

Or for populated CSV files (in the release_populated directory):

.. code-block:: bash

    flatten-tool unflatten release_populated --root-id=ocid --base-json base.json --input-format csv --output-name release.json --root-list-path=releases

These produce a release.json file based on the data in the spreadsheets.

See ``flatten-tool unflatten --help`` for details of the command line options.

.. _ocds-cli-templates:

Creating spreadsheet templates
------------------------------

Download https://raw.githubusercontent.com/open-contracting/standard/1.0/standard/schema/release-schema.json to the current directory.

.. code-block:: bash

    flatten-tool create-template --root-id=ocid --schema release-schema.json --main-sheet-name releases

This will create ``template.xlsx`` and a ``template/`` directory of CSV files.

See ``flatten-tool create-template --help`` for details of the command line options.

