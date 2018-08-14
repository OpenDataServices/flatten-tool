# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Prefer `RootListPath` from sheet configuration over CLI/function argument https://github.com/OpenDataServices/flatten-tool/pull/214

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
- Do not hardcode iati-activities for top level for all xml https://github.com/OpenDataServices/flatten-tool/issues/150
- Don't split text value of xml array https://github.com/OpenDataServices/flatten-tool/pull/208

## [0.1.1] - 2018-03-28

Initial Release.
