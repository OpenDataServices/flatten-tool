Flatten-Tool [Alpha]
============

[![Build Status](https://travis-ci.org/OpenDataServices/flatten-tool.svg?branch=master)](https://travis-ci.org/OpenDataServices/flatten-tool)
[![Coverage Status](https://img.shields.io/coveralls/OpenDataServices/flatten-tool.svg)](https://coveralls.io/r/OpenDataServices/flatten-tool?branch=master)
[![Code Health](https://landscape.io/github/OpenDataServices/flatten-tool/master/landscape.png)](https://landscape.io/github/OpenDataServices/flatten-tool/master)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/OpenDataServices/flatten-tool/blob/master/LICENSE)

Flatten-Tool is a general purpose tool with the goal of allowing a dataset to be round-tripped between structured JSON and tabular data packages or spreadsheets: providing a bridge between richly structured datasets and accessible flat formats. 

It was developed for use with the [Open Contracting Data Standard](http://standard.open-contracting.org), and has been further developed with the [360 Giving Data Standard](http://www.threesixtygiving.org/standard/reference/). We're keen to see if it is useful in other contexts too. 

It is also used in to power the [COnvert Validate Explore (COVE) tool](https://github.com/OpenDataServices/cove) which provides a web interface for Flatten-Tool configured against a particular JSON Schema. 

## Features

* Convert data from a "flat" spreadsheet into structured form;
* Take JSON data and provide a flattened output;
* Generate a template Excel or CSV file based on a JSON Schema;
* Use a JSON schema to guide the approach to flattening; 
* Use a JSON schema to provide column titles rather than field names;

## Examples

The JSON [examples/simple.json](examples/simple.json):

```json
{
    "main": [
        {
            "a": {
                "b": "1",
                "c": "2"
            },
            "d": "3"
        },
        {
            "a": {
                "b": "4",
                "c": "5"
            },
            "d": "6"
        }
    ]
}
```

Can be converted to/from a spreadsheet like [examples/simple/main.csv](examples/simle/main.csv):

|a/b|a/c|d  |
|---|---|---|
|1  |2  |3  |
|4  |5  |6  |


Using the commands:

```
flatten-tool unflatten -f csv examples/simple -o examples/simple.json
flatten-tool flatten -f csv examples/simple.json -o examples/simple
```




### One to many relationships (JSON arrays)

There are multiple shapes of spreadsheet that can be used to produce the same JSON arrays. E.g. to produce this JSON:

```json
{
    "main": [
        {
            "id": "1",
            "a": [
                {
                    "b": "2",
                    "c": "3"
                },
                {
                    "b": "4",
                    "c": "5"
                }
            ],
            "d": "6"
        },
        {
            "id": "7",
            "a": [
                {
                    "b": "8",
                    "c": "9"
                },
                {
                    "b": "10",
                    "c": "11"
                }
            ],
            "d": "12"
        }
    ]
}
```

we can use these Spreadsheets:

|id|d|
|---|---|
|1|6|
|7|12|


|id|a/0/b|a/0/c|
|---|---|---|
|1|2|3|
|1|4|5|
|7|8|9|
|7|10|11|


These are also the spreadsheets that flatten-tool's `flatten` (JSON to Spreadsheet) will produce.

Commands used to generate this:

```
flatten-tool unflatten -f csv examples/array_multisheet -o examples/array_multisheet.json
flatten-tool flatten -f csv examples/array.json -o examples/array_multisheet
```

However, there are other "shapes" of spreadsheet that can produce the same JSON.

New columns for each item of the array:

|id|a/0/b|a/0/c|a/1/b|a/1/c|d|
|---|---|---|---|---|---|
|1|2|3|4|5|6|
|7|8|9|10|11|12|

```
flatten-tool unflatten -f csv examples/array_pointer -o examples/array.json
```

Repeated rows:

|id|a/0/b|a/0/c|d|
|---|---|---|---|
|1|2|3|6|
|1|4|5|6|
|7|8|9|12|
|7|10|11|12|


```
flatten-tool unflatten -f csv examples/array_repeat_rows -o examples/array.json
```


### Arrays within arrays

```
{
    "main": [
        {
            "id": "1",
            "d": "6",
            "a": [
                {
                    "id": "2",
                    "b": [
                        {
                            "c": "3"
                        },
                        {
                            "c": "3a"
                        }
                    ]
                },
                {
                    "id": "4",
                    "b": [
                        {
                            "c": "5"
                        },
                        {
                            "c": "5a"
                        }
                    ]
                }
            ]
        },
        {
            "id": "7",
            "d": "12",
            "a": [
                {
                    "id": "8",
                    "b": [
                        {
                            "c": "9"
                        },
                        {
                            "c": "9a"
                        }
                    ]
                },
                {
                    "id": "10",
                    "b": [
                        {
                            "c": "11"
                        },
                        {
                            "c": "11a"
                        }
                    ]
                }
            ]
        }
    ]
}
```

|id|d|
|---|---|
|1|6|
|7|12|

|id|a/0/id|
|---|---|
|1|2|
|1|4|
|7|8|
|7|10|

|id|a/0/id|a/0/b/0/c|
|---|---|---|
|1|2|3|
|1|2|3a|
|1|4|5|
|1|4|5a|
|7|8|9|
|7|8|9a|
|7|10|11|
|7|10|11a|

### Why
Imagine a simple dataset that describes grants. Chances are if is to represent the world, it is going to need to contain some one-to-many relationships (.e.g. one grant, many categories). This is structured data. 

But, consider two audiences for this dataset:

**The developer** wants structured data that she can iterate over, one record for each grant, and then the classifications nested inside that record. 

**The analyst** needs flat data - tables that can be sorted, filtered and explored in a spreadsheet. 

Which format should the data be published in? Flattten-Tool thinks it should be both. 

By introducing a couple of simple rules, Flatten-Tool is aiming to allow data to be round-tripped between JSON and flat formats, sticking to sensible idioms in both flat-land and a structured world. 

### How 

Flatten-Tool was designed to work along with a JSON Schema. Flatten-Tool likes
JSON Schemas which:

**(1) Provide an ```id``` at every level of the structure**

So that each entity in the data structure can be referenced easily in the flat
version. It turns out this is also pretty useful for JSON-LD mapping.

**(2) Describes the ideal root table by rolling up properties**

Often in a data structure, there are only a few properties that exist at the
root level, with most properties at least one level deep in the structure.
However, if Flatten-Tool hides away all the important properties in sub tables,
then the spreadsheet user has to hunt all over the place for the properties
that matter to them.

So, we introduce a custom 'rollUp' property to out JSON Schema. This allows the
schema to specify which relationships and properties should be included in the
first table of a spreadsheet.

You can even roll up fields which *could* be one-to-many, but which often will
be one-to-one relationships, so that there is a good chance of a user of the
flattened data being able to do all the data creation or analysis they want in
a single table.

**(3) Provide unique field titles**

"Recipient Org: Name" is a lot friendlier to spreadsheet users than
'receipientOrganisation/name'. So, Flatten-Tool includes support for using the
titles of JSON fields instead of the field names when creating a spreadsheet
template and converting data.

But - to make that use, the titles at each level of the structure do need to be
unique.

**(4) Don't nest too deep**

Whilst Flatten-Tool can cope with multiple laters of nesting in a data
structure, the deeper the structure gets, the trickier it is for the
spreadsheet user to understand what is going on. So, we try and just go a few
layers deep at most in data for Flatten-Tool to work with. 




## Technical details of how it works...

Type information:
* If we have a JSON schema, we use the type information from that
Without a JSON schema
* For an Excel spreadsheet we get some type information (e.g. strings vs numbers).
* For a CSV everything is strings

Python Version Support
----------------------

This code supports Python 2.7 and Python 3.3 (and later). Python 3 is
strongly preferred. Only servere Python 2 specific bugs will be fixed, see the
[python2-wontfix](https://github.com/OpenDataServices/flatten-tool/issues?q=is%3Aissue+label%3Apython2-wontfix+is%3Aclosed)
label on GitHub for known minor issues.

Python 2.6 and earlier are not supported at all because our code makes use new
language constructs introduced in Python 3 and 2.7. Python 3.2 (also 3.1 and
3.0) is not supported, because one of the dependencies (openpyxl) does not
support it.

Installation
------------

    git clone https://github.com/OpenDataServices/flatten-tool.git
    cd flatten-tool
    virtualenv -p $(which python3) .ve
    source .ve/bin/activate
    pip install -r requirements_dev.txt

Usage
-----

    flatten-tool -h

will print general help information.

    flatten-tool {create-template,unflatten} -h

will print help information specific to that subcommand.


## Usage for OCDS

You can also upload the file to http://standard.open-contracting.org/validator/

### Creating spreadsheet templates

Download https://raw.githubusercontent.com/open-contracting/standard/1.0/standard/schema/release-schema.json to the current directory.

    flatten-tool create-template --root-id=ocid --output-format all --output-name template --schema release-schema.json --main-sheet-name releases

This will create `template.xlsx` and a `template/` directory of csv files.

See `flatten-tool --help` for details of the commandline options.


### Converting a populated spreadsheet to JSON

    cp base.json.example base.json

And populate this with the package information for your release.

Then, for a populated xlsx template in (in release_populated.xlsx):

    flatten-tool unflatten release_populated.xlsx --root-id=ocid --base-json base.json --input-format xlsx --output-name release.json --root-list-path='releases'

Or for populated CSV files (in the release_populated directory):

    flatten-tool unflatten release_populated --root-id=ocid --base-json base.json --input-format csv --output-name release.json --root-list-path='releases'

These produce a release.json file based on the data in the spreadsheets.


### Converting a JSON file to a spreadsheet

    flatten-tool flatten input.json --root-id=ocid --main-sheet-name releases --output-name flattened --root-list-path='releases'

This will create `flattened.xlsx` and a `flattened/` directory of csv files.

## Usage for 360Giving

You can also upload the file to http://cove.opendataservices.coop/360

Download
https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json
to the current directory.

    flatten-tool create-template --output-format all --output-name 360giving-template --schema 360-giving-schema.json --main-sheet-name grants --rollup --use-titles

    flatten-tool unflatten -o out.json -f xlsx input.xlsx --schema 360-giving-schema.json --convert-titles --root-list-path='grants'


Running the tests
-----------------

After following the installation above, run `py.test`.

Note that the tests require the Python testsuite. This should come with python,
but some distros split it out. On Ubuntu you will need to install a package
like `libpython3.4-testsuite` (depending on which Python version you are
using).

Encodings
---------

The encoding of input CSVs can be specified with the `--encoding` flag. This
can be any encoding recognised by Python:
https://docs.python.org/2/library/codecs.html#standard-encodings

However, Python 2 can not load CSVs that contain the NULL character. This
includes CSVs encoded in UTF-16. If you wish to convert UTF-16 encoded CSVs you
must use Python 3.

(See [this
test](https://github.com/OpenDataServices/flatten-tool/blob/61d8404b444f10384363cde1cad542a0d04af004/flattentool/tests/test_input.py#L130)
which passes for Python 3, but fails for Python 2).


