Flatten-Tool (aka Flat Stan) [Alpha]
============

[![Build Status](https://travis-ci.org/OpenDataServices/flatten-tool.svg?branch=master)](https://travis-ci.org/OpenDataServices/flatten-tool)
[![Coverage Status](https://img.shields.io/coveralls/OpenDataServices/flatten-tool.svg)](https://coveralls.io/r/OpenDataServices/flatten-tool?branch=master)
[![Code Health](https://landscape.io/github/OpenDataServices/flatten-tool/master/landscape.png)](https://landscape.io/github/OpenDataServices/flatten-tool/master)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/OpenDataServices/flatten-tool/blob/master/LICENSE)

Flat Stan is a general purpose tool with the goal of allowing a dataset to be round-tripped between structured JSON and tabular data packages or spreadsheets: providing a bridge between richly structured datasets and accessible flat formats. 

It was developed for use with the [Open Contracting Data Standard](http://standard.open-contracting.ogr), and has been further developed with the [360 Giving Data Standard](http://docs.threesixtygiving.ogr). We're keen to see if it is useful in other contexts too. 

It is also used in to power the [COnvert Validate Explore (COVE) tool](https://github.com/OpenDataServices/cove) which provides a web interface for Flat Stan configured against a particular JSON Schema. 

## Features

* Generate a template Excel or CSV file based on a JSON Schema;
* Convert data from flat template into structured form;
* Take JSON data and provide a flattened output;
* Use a JSON schema to guide the approach to flattening; 
* Use a JSON schema to provide column titles rather than field names;

ToDo:

[ ] Improve documentation;
[ ] Improve round-tripping of data;
[ ] Add support for [Data Packages](http://data.okfn.org/doc/data-package) as an input/output option;
[ ] Add support for annotation of columns and adding validation to Excel spreadsheet templates;
[ ] Add multi-lingual support for field titles

### Why
Imagine a simple dataset that describes grants. Chances are if is to represent the world, it is going to need to contain some one-to-many relationships (.e.g. one grant, many categories). This is structured data. 

But, consider two audiences for this dataset:

**The developer** wants structured data that she can iterate over, one record for each grant, and then the classifications nested inside that record. 

**The analyst** needs flat data - tables that can be sorted, filtered and explored in a spreadsheet. 

Which format should the data be published in? Flat Stan thinks it should be both. 

By introducing a couple of simple rules, Flat Stan is aiming to allow data to be round-tripped between JSON and flat formats, sticking to sensible idioms in both flat-land and a structured world. 

### How 

Flat Stan was designed to work along with a JSON Schema. Flat Stan likes JSON Schemas which:

**(1) Provide a ```id``` at every level of the structure**

So that each entity in the data structure can be referenced easily in the flat version. It turns out this is also pretty useful for JSON-LD mapping.

**(2) Re-use common blocks of schema...**

...where it would make sense for the items described to all be gathered in one flattened table.

For example, if you have a fundingOrganisation, and a recipientOrganisation for a grant, both can be represented in the JSON schema as references to an chunk of 'Organisation' schema. Flat Stan will then create a single Organisation table, and will use a reference column to identify the kind of organisation we are dealing with. 

This keeps the spreadsheets simpler. Whether or not gathering receipientOrganisation and fundingOrganisation together is a design decision based on how you expect the flat version of the data to be used. 

**(3) Describes the ideal root table by rolling up properties **

Often in a data structure, there are only a few properties that exist at the root level, with most properties at least one level deep in the structure. However, if Flat Stan hides away all the important properties in sub tables, then the spreadsheet user has to hunt all over the place for the properties that matter to them.

So, we introduce a custom 'rollUp' property to out JSON Schema. This allows the schema to specify which relationships and properties should be included in the first table of a spreadsheet.

You can even roll up fields which *could* be one-to-many, but which often will be one-to-one relationships, so that there is a good chance of a user of the flattened data being able to do all the data creation or analysis they want in a single table.

**(4) Provide unique field titles **

"Recipient Org: Name" is a lot friendlier to spreadsheet users than 'receipientOrganisation/name'. So, Flat Stan includes support for using the titles of JSON fields instead of the field names when creating a spreadsheet template and converting data.

But - to make that use, the titles at each level of the structure do need to be unique.

**(5) Don't nest too deep **

Whilst Flat Stan can cope with multiple laters of nesting in a data structure, the deeper the structure gets, the trickier it is for the spreadsheet user to understand what is going on. So, we try and just go a few layers deep at most in data for Flat Stan to work with. 




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
