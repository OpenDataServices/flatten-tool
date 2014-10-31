Flattening OCDS
===============

Installation
------------

    git clone https://github.com/open-contracting/flattening-ocds.git
    virtualenv pyenv
    source pyenv/bin/activate
    pip install -r requirements.txt

Usage
-----

Paths are currently hardcoded.

Download https://raw.githubusercontent.com/open-contracting/standard/master/standard/schema/release-schema.json to the current directory.

    python spread.py

This will create `release.xlsx` and a `release/` directory of csv files.
