# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Some typos in docs, comments and examples
- Put back some translations that were removed
- Minor python tidyups
- Avoid deprecation warning from the ijson package.  https://github.com/OpenDataServices/flatten-tool/pull/458

### Removed

- We no longer support Python 3.7 - security support has ended
- We no longer support Python 3.8 - security support ends 31 Oct 2024

## [0.26.0] - 2024-08-22

### Fixed

- Ignore null characters in the input CSV file when getting non-header rows
- When unflatteneing XML, avoid errors due to namespaces causing colons in sheet names, by replacing them with dashes https://github.com/OpenDataServices/flatten-tool/pull/456

### Changed

- Use custom warnings and exceptions [#450](https://github.com/OpenDataServices/flatten-tool/issues/450) [#451](https://github.com/OpenDataServices/flatten-tool/issues/451)
- Add example pip install command to geo dependencies missing warning [#445](https://github.com/OpenDataServices/flatten-tool/issues/445)
- When outputting XML, handle namespaces that don't cover the whole file https://github.com/OpenDataServices/flatten-tool/pull/456

## [0.25.0] - 2024-07-05

### Fixed

- Don't error when there's a datetime in the header https://github.com/OpenDataServices/flatten-tool/issues/438

- Ignore null characters in the input CSV file when reading configuration from the header rows
  https://github.com/OpenDataServices/flatten-tool/pull/446

### Changed

- If `json_dict` is not a dict, return a useful error/warning https://github.com/OpenDataServices/flatten-tool/issues/442

## [0.24.2] - 2024-06-12

### Fixed

- Rename `_get_column_letter` import to `get_colunmn_letter` for compatibility
  with latest openpyxl
  https://github.com/OpenDataServices/flatten-tool/issues/443

## [0.24.1] - 2024-02-09

### Fixed

- Ignore null characters in the input CSV file when getting header rows
  https://github.com/OpenDataServices/flatten-tool/pull/435

## [0.24.0] - 2023-11-15

### Changed

- New "geo" optional python dependency and some existing python dependencies moved to it.
  If you were using this functionality before, you'll need to start installing "geo"  to get same behaviour.
  https://github.com/OpenDataServices/flatten-tool/issues/424
  https://github.com/OpenDataServices/flatten-tool/pull/433

## [0.23.0] - 2023-08-30

### Changed

- Flatten & Create Template: Previously, CSV filenames were truncated to 31 characters, which is the maximum length of a sheet name in Excel.
  Now allow CSV filenames of any length and only truncate sheet names when the output format is XLSX or ODS.
  https://github.com/OpenDataServices/flatten-tool/pull/428

### Fixed

- flatten --sheet-prefix option does not work in ODS files https://github.com/OpenDataServices/flatten-tool/issues/430

## [0.22.0] - 2023-06-27

### Added

- Generate templates that are correct for WKT <-> geojson conversion

## [0.21.0] - 2023-06-23

### Added

- WKT <-> geojson conversion for flattening and unflattening, behind an optional flag https://github.com/OpenDataServices/flatten-tool/issues/419

### Removed

- We no longer support Python 3.6

## [0.20.1] - 2023-01-11

### Fixed

- Import backports-datetime-fromisoformat only if needed, to fix PyPy 3.7 support

## [0.20.0] - 2022-12-07

### Changed

- Add `--line-terminator` option to `flatten` and `create-template`

## [0.19.0] - 2022-11-16

### Fixed

- Make work with multiple versions of jsonref

## [0.18.1] - 2022-10-28

### Fixed

- Lock to a version of jsonref<1 to avoid breaking changes in 1.0.0

## [0.18.0] - 2022-09-26

- Add support for flattening an array of arrays https://github.com/OpenDataServices/flatten-tool/issues/398

## [0.17.2] - 2022-06-15

### Fixed

- Handle extensions in the schema xsd correctly when sorting https://github.com/OpenDataServices/cove/issues/1366

## [0.17.1] - 2021-07-21

### Fixed

- Use backports-datetime-fromisoformat only if needed, to fix PyPy 3.7 support https://github.com/OpenDataServices/flatten-tool/pull/386

## [0.17.0] - 2021-04-27

### Removed

- We no longer support Python 3.5

### Fixed

- Don't fail when an .ods column header is empty https://github.com/OpenDataServices/flatten-tool/issues/378

## [0.16.0] - 2021-03-24

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
