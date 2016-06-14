Developer Guide
+++++++++++++++

The primary use case for Flatten Tool is to convert spreadsheets to JSON so
that the data can be validated using a `JSON Schema
<http://json-schema.org/documentation.html>`_.

Flatten Tool has to be very forgiving in what it accepts so that it can deal
with spreadsheets that are a work-in-progress. It tries its best to make
sense of what you give it, even if you give it inconsistent, conflicting or
patchy data. It leaves the work of reporting problems to the JSON Schema
validator that will be run on the JSON it produces, and it only generates
warnings if it is forced to ignore data from the source spreadsheet.

Flatten Tool tries its best to ouput as much as it can so the JSON it produces
will be as good or bad as the spreadsheet input it receives. The benefit of
this approach that the user can be shown all the problems in one go when the
JSON Schema validator is run on that JSON.

Programming a very forgiving tool that tries to accept lots of categories of
errors is a lot more complex than programming a tool where the data strucutres
are very predictable. Understanding this intention not to raise errors is key
to understanding Flatten Tool's internal design.

Helper Libraries
================

As you'll have read in the :doc:`User Guide <userguide>`, Flatten Tool makes
use of JSON Pointer, JSON Schema and JSON Ref standards. The Python libraries
that support this are `jsonpointer`, `jsonschema` and `jsonref` respectively.
