Flattening OCDS
===============

[![Build Status](https://travis-ci.org/open-contracting/flattening-ocds.svg?branch=master)](https://travis-ci.org/open-contracting/flattening-ocds)
[![Code Health](https://landscape.io/github/open-contracting/flattening-ocds/master/landscape.png)](https://landscape.io/github/open-contracting/flattening-ocds/master)

Python Version Support
----------------------

This code supports Python 2.7 and Python 3.3 (and later).

Python 2.6 and earlier are not supported because our code makes use new language constructs introduced in Python 3 and 2.7. Python 3.2 (also 3.1 and 3.0) is not supported, because one of the dependencies (openpyxl) does not support it.

Installation
------------

    git clone https://github.com/open-contracting/flattening-ocds.git
    cd flattening-ocds
    virtualenv pyenv
    source pyenv/bin/activate
    pip install -r requirements_dev.txt

Usage
-----

    flatten-ocds

will print general help information.

    flatten-ocds {create-template,unflatten} -h

will print help information specific to that subcommand.


### Creating spreadsheet templates

Download https://raw.githubusercontent.com/open-contracting/standard/master/standard/schema/release-schema.json to the current directory.

    flatten-ocds create-template --output-format all --output-name release --schema release-schema.json --main-sheet-name release

This will create `release.xlsx` and a `release/` directory of csv files.

See `flatten-ocds --help` for details of the commandline options.

### Converting a populated spreadsheet to JSON

    cp base.json.example base.json

And populate this with the package information for your release.

Then, for a populated xlsx template in (in release_populated.xlsx):

    flatten-ocds unflatten release_populated.xlsx --base-json base.json --input-format xlsx --output-name release.json  

Or for populated CSV files (in the release_populated directory):

    flatten-ocds unflatten release_populated --base-json base.json --input-format csv --output-name release.json  

These produce a release.json file based on the data in the spreadsheets.


Encodings
---------

The encoding of input CSVs can be specified with the `--encoding` flag. This can be any encoding recognised by Python: https://docs.python.org/2/library/codecs.html#standard-encodings

However, Python 2 can not load CSVs that contain the NULL character. This includes CSVs encoded in UTF-16. If you wish to convert UTF-16 encoded CSVs you must use Python 3.

(See [this test](https://github.com/open-contracting/flattening-ocds/blob/d7db1125fef079302dcd372593c471c527aff7fb/flattening_ocds/tests/test_input.py#L114) which passes for Python 3, but fails for Python 2).
