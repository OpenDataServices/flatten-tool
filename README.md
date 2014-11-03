Flattening OCDS
===============

[![Build Status](https://travis-ci.org/open-contracting/flattening-ocds.svg?branch=master)](https://travis-ci.org/open-contracting/flattening-ocds)
[![Code Health](https://landscape.io/github/open-contracting/flattening-ocds/master/landscape.png)](https://landscape.io/github/open-contracting/flattening-ocds/master)

Installation
------------

    git clone https://github.com/open-contracting/flattening-ocds.git
    virtualenv pyenv
    source pyenv/bin/activate
    pip install -r requirements_dev.txt

Usage
-----

Paths are currently hardcoded.

Download https://raw.githubusercontent.com/open-contracting/standard/master/standard/schema/release-schema.json to the current directory.

    flatten-ocds

This will create `release.xlsx` and a `release/` directory of csv files.
