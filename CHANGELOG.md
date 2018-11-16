# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A -v verbose option to the cli to generate more verbose output.

### Changed

- Output on the command line is not by default less verbose


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
