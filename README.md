Flatten Tool
============

[![Build Status](https://travis-ci.org/OpenDataServices/flatten-tool.svg?branch=master)](https://travis-ci.org/OpenDataServices/flatten-tool)
[![Coverage Status](https://img.shields.io/coveralls/OpenDataServices/flatten-tool.svg)](https://coveralls.io/r/OpenDataServices/flatten-tool?branch=master)
[![Code Health](https://landscape.io/github/OpenDataServices/flatten-tool/master/landscape.png)](https://landscape.io/github/OpenDataServices/flatten-tool/master)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/OpenDataServices/flatten-tool/blob/master/LICENSE)

Python Version Support
----------------------

This code supports Python 2.7 and Python 3.3 (and later).

Python 2.6 and earlier are not supported because our code makes use new language constructs introduced in Python 3 and 2.7. Python 3.2 (also 3.1 and 3.0) is not supported, because one of the dependencies (openpyxl) does not support it.

Installation
------------

    git clone https://github.com/OpenDataServices/flatten-tool.git
    cd flatten-tool
    virtualenv pyenv
    source pyenv/bin/activate
    pip install -r requirements_dev.txt

Usage
-----

    flatten-tool -h

will print general help information.

    flatten-tool {create-template,unflatten} -h

will print help information specific to that subcommand.


### Creating spreadsheet templates

Download https://raw.githubusercontent.com/open-contracting/standard/master/standard/schema/release-schema.json to the current directory.

    flatten-tool create-template --output-format all --output-name template --schema release-schema.json --main-sheet-name releases

This will create `template.xlsx` and a `template/` directory of csv files.

See `flatten-tool --help` for details of the commandline options.


### Converting a populated spreadsheet to JSON

    cp base.json.example base.json

And populate this with the package information for your release.

Then, for a populated xlsx template in (in release_populated.xlsx):

    flatten-tool unflatten release_populated.xlsx --base-json base.json --input-format xlsx --output-name release.json  

Or for populated CSV files (in the release_populated directory):

    flatten-tool unflatten release_populated --base-json base.json --input-format csv --output-name release.json  

These produce a release.json file based on the data in the spreadsheets.


### Converting a JSON file to a spreadsheet

    flatten-tool flatten input.json --main-sheet-name release --output-name unflattened

This will create `unflattened.xlsx` and a `unflattened/` directory of csv files.



Encodings
---------

The encoding of input CSVs can be specified with the `--encoding` flag. This can be any encoding recognised by Python: https://docs.python.org/2/library/codecs.html#standard-encodings

However, Python 2 can not load CSVs that contain the NULL character. This includes CSVs encoded in UTF-16. If you wish to convert UTF-16 encoded CSVs you must use Python 3.

(See [this test](https://github.com/OpenDataServices/flatten-tool/blob/d7db1125fef079302dcd372593c471c527aff7fb/flattentool/tests/test_input.py#L114) which passes for Python 3, but fails for Python 2).


360 Giving Support
------------------

There is work currently in progress to convert this codebase to also flatten 360 giving files.

Download https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json to the current directory.

    flatten-tool create-template --root-id='' --output-format all --output-name 360giving-template --schema 360-giving-schema.json --main-sheet-name grants --rollup --use-titles

    flatten-tool unflatten --root-id='' -o out.json -f xlsx --main-sheet-name=grants input.xlsx --schema 360-giving-schema.json --convert-titles
