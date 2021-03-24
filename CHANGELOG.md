# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fix another number formatting .ods bug https://github.com/OpenDataServices/flatten-tool/pull/383

### Changed

- Reduce memory footprint of flattening https://github.com/OpenDataServices/flatten-tool/pull/376

## [0.15.4] - 2021-03-08

### Fixed

- Fix parsing date and number formatting from .ods files https://github.com/OpenDataServices/flatten-tool/pull/373

## [0.15.3] - 2021-02-23

### Fixed

- flattening: Uses much less memory by storing data in a embedded ZODB database, using ijson and using write only mode in pyopenxl.
- use-titles: Use $ref'erring title if available https://github.com/OpenDataServices/flatten-tool/pull/368 
- create-template --no-deprecated-fields: Did not work if deprecated element at same level as a $ref https://github.com/OpenDataServices/flatten-tool/issues/185#issuecomment-719587348

## [0.15.2] - 2020-10-29

### Fixed

- Don't fail if compiled translation files (.mo) don't exist, and Django isn't installed
- Fix some incorrect assumptions about types
- Allow XML IDs to be attributes

## [0.15.1] - 2020-10-21

### Fixed

- Don't fail if compiled translation files (.mo) don't exist

## [0.15.0] - 2020-10-19

### Added

- Add Spanish translation for all strings that could appear in the CoVE web UI https://github.com/OpenDataServices/flatten-tool/pull/362

## [0.14.0] - 2020-09-29

### Fixed

- Fix use of titles for sheet names, to avoid KeyError when a field is missing from the schema

### Changed

- Include sheet name with duplicate heading warnings.

## [0.13.0] - 2020-09-09

### Changed

- When `--use-titles` is specified, also use the titles for sheet names (ie. Excel tabs and CSV filenames)

## [0.12.0] - 2020-08-25

### Added

- Add support for `"format": "date"` in a JSON schema

### Changed

- All code has had black and isort applied. These have been added to Travis.

## Fixed

- Remove extra lines in CSVs under Windows https://github.com/OpenDataServices/flatten-tool/pull/350

## [0.11.0] - 2020-02-21

### Added

- Add .ods (OpenDocument Spreadsheet) file format support https://github.com/OpenDataServices/flatten-tool/pull/326

## [0.10.0] - 2020-02-06

### Changed

- Drop Python 2 support https://github.com/OpenDataServices/flatten-tool/issues/299
- Documentation on Change Logs, Versioning and PyPi updated to match current practice.

## Fixed

- Add BadXLSXZipFile exception type for BadZipFile exception when handling broken XLSX files related to cove issue https://github.com/OpenDataServices/cove/issues/514

## [0.9.0] - 2019-08-11

### Added

- Add an XML declaration to outputted XML files https://github.com/OpenDataServices/cove/issues/1206


## [0.8.0] - 2019-07-31

### Added

- --preserve-fields option to the cli so the user can specify which fields to keep when flattening, instead of defaulting to all of them

## Fixed

- Correct cell source map when hashcomments is used.

### Changed

- Using --rollup with `flatten` accepts fields to roll up as input directly and via a file, as well as via a schema.
- Fixed pytest version at <5 because of breaking changes to the tests.

## [0.7.0] - 2019-04-08

## Fixed

- Ignore NoneType in json instead of giving a TypeError.

## [0.6.0] - 2019-03-25

### Added

- A -v verbose option to the cli to generate more verbose output.
- A --truncation-length option to create-template and flatten
- A --no-deprecated-fields option to create-template.

### Changed

- Output on the command line is by default less verbose
- openpyxl of at least 2.6 is required https://github.com/OpenDataServices/flatten-tool/issues/287
- For Python 3, 3.5 or later is required
- (XML only) Ensure the same path isn't split across multiple sheets - https://github.com/OpenDataServices/flatten-tool/pull/293

## [0.5.0] - 2018-11-13

### Added

- While trying to decode JSON, if there is a UTF8 error raise the new exception class BadlyFormedJSONErrorUTF8.
  (This extends the old BadlyFormedJSONError exception, so existing code that checks sensibly should be fine.)

## [0.4.0] - 2018-11-07

### Added

- Add --disable-local-refs to flatten, unflatten and create-template.
- Add --remove-empty-schema-columns flag to flatten  https://github.com/OpenDataServices/cove/issues/1019
- Add --xml-comment to unflatten.

### Changed

- Commands from command line overridden individually by commands in the metatab. Previously all commands taken from metatab and the rest ignored if only one was added.

### Fixed

- In setup.py, set author and author_email to general values.

### Fixed

- create-template: If --output-format is xlsx, the default --output-name is template.xlsx instead of template.
- flatten: If --output-format is xlsx, the default --output-name is flattened.xlsx instead of flattened.

## [0.3.0] - 2018-10-12

### Added

- Add a spreadsheet configuration variable for id_name (called IDName).
- Add --root-is-list to flatten and unflatten.
- Add --sheet-prefix to flatten.
- Add --filter-field and --filter-value to flatten.
- Added new BODS page to docs.

### Fixed

- Ignore elements that don't exist in the schema, whilst sorting XML. Previously an exception was raised. https://github.com/OpenDataServices/flatten-tool/pull/218
- Fix: unflatten would crash if given a csv with an empty first row https://github.com/OpenDataServices/flatten-tool/pull/229
- Clarified meaning of headerrows in docs. https://github.com/OpenDataServices/flatten-tool/issues/230
- Tool can work with schemas that have refs to local files (part of https://github.com/OpenDataServices/flatten-tool/issues/225 )
- Schema loader can work with schemas that have 'oneOf' (part of https://github.com/OpenDataServices/flatten-tool/issues/225 )

## [0.2.0] - 2018-08-13

### Added

- Sort XML according to provided schema(s) https://github.com/OpenDataServices/flatten-tool/pull/196

### Changed

- Remove Python 3.3 support https://github.com/OpenDataServices/flatten-tool/commit/636cf988ff7e5247a089b22061f0fe7767ea81b4

### Fixed

- Avoid some openpyxl warnings https://github.com/OpenDataServices/flatten-tool/pull/211
- Fix XML unflattening with stdlib etree https://github.com/OpenDataServices/flatten-tool/pull/212

## [0.1.2] - 2018-06-28

(As there are new features, this should have been a minor release. Just noting so we pick this up for future releases.)

(This release was documented after the release and some things may have been missed.)

### Added

- Support user-defined XML root node https://github.com/OpenDataServices/flatten-tool/pull/201
- Require lxml https://github.com/OpenDataServices/flatten-tool/pull/207

### Fixed

- Add missing comma to CSV fixture https://github.com/OpenDataServices/flatten-tool/pull/203
- Do not hard code iati-activities for top level for all XML https://github.com/OpenDataServices/flatten-tool/issues/150
- Don't split text value of XML array https://github.com/OpenDataServices/flatten-tool/pull/208

## [0.1.1] - 2018-03-28

Initial Release.
