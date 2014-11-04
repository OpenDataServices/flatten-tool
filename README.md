Flattening OCDS
===============

[![Build Status](https://travis-ci.org/open-contracting/flattening-ocds.svg?branch=master)](https://travis-ci.org/open-contracting/flattening-ocds)
[![Code Health](https://landscape.io/github/open-contracting/flattening-ocds/master/landscape.png)](https://landscape.io/github/open-contracting/flattening-ocds/master)

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
