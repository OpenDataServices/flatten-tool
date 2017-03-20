Flatten-Tool [Beta]
===================

[![Build Status](https://travis-ci.org/OpenDataServices/flatten-tool.svg?branch=master)](https://travis-ci.org/OpenDataServices/flatten-tool)
[![Coverage Status](https://img.shields.io/coveralls/OpenDataServices/flatten-tool.svg)](https://coveralls.io/r/OpenDataServices/flatten-tool?branch=master)
[![Code Health](https://landscape.io/github/OpenDataServices/flatten-tool/master/landscape.png)](https://landscape.io/github/OpenDataServices/flatten-tool/master)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/OpenDataServices/flatten-tool/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/flatten-tool/badge/?version=latest)](http://flatten-tool.readthedocs.io/en/latest/?badge=latest)

[Flatten-Tool](http://flatten-tool.readthedocs.io/en/latest/) is a general purpose tool with the goal of allowing a dataset to be round-tripped between structured JSON and tabular data packages or spreadsheets: providing a bridge between richly structured datasets and accessible flat formats. 

It was developed for use with the [Open Contracting Data Standard](http://standard.open-contracting.org), and has been further developed with the [360 Giving Data Standard](http://www.threesixtygiving.org/standard/reference/). We're keen to see if it is useful in other contexts too. 

It is also used in to power the [COnvert Validate Explore (COVE) tool](https://github.com/OpenDataServices/cove) which provides a web interface for Flatten-Tool configured against a particular JSON Schema. 

For more information see the [Flatten-Tool docs](http://flatten-tool.readthedocs.io/en/latest/).

## Features

* Convert data from a "flat" spreadsheet into structured form;
* Take JSON data and provide a flattened output;
* Generate a template Excel or CSV file based on a JSON Schema;
* Use a JSON schema to guide the approach to flattening; 
* Use a JSON schema to provide column titles rather than field names;

For more information see the [Flatten-Tool docs](http://flatten-tool.readthedocs.io/en/latest/).

## Quick Example

For more examples see http://flatten-tool.readthedocs.io/en/latest/examples/

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

Can be converted to/from these spreadsheets:

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

For more examples see http://flatten-tool.readthedocs.io/en/latest/examples/
