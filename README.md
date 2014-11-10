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

Download https://raw.githubusercontent.com/open-contracting/standard/master/standard/schema/release-schema.json to the current directory.

    flatten-ocds --output-name release create-template --schema release-schema.json --main-sheet-name release

This will create `release.xlsx` and a `release/` directory of csv files.

See `flatten-ocds --help` for details of the commandline options.
