.. Flatten Tool documentation master file, created by
   sphinx-quickstart on Tue Jun 14 09:45:14 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flatten Tool's documentation!
========================================

.. caution::

   This documentation is a work in progress.

Flatten Tool is a Python library and command line interface for converting
single or multi-sheet spreadsheets to a JSON document and back again. In
Flatten Tool terminology *flattening* is the process of converting a JSON
document to spreadsheet sheets, and *unflattening* is the process of converting
spreadsheet sheets to a JSON document.

Flatten Tool can make use of a JSON Schema during the flattening and
unflattening processes to make sure different types are handled correctly, to
support more human-friendly column headings and to give hints about the
spreadsheet structure you would like.

Flatten Tool's main use case is to allow people to enter data into a
spreadsheet so that it can be converted to a JSON document and validated
against a JSON Schema. To support this use case it is very forgiving in what it
accepts and prefers to output as much of the input spreadsheet data as it can
to be validated by a JSON Schema later, rather than raise errors itself.

Contents:

.. toctree::
   :maxdepth: 4

   introduction
   examples
   getting-started
   unflatten
   create-template
   flatten
   developerguide
   usage-ocds
   usage-360

Get started by reading the Spreadsheet Designer's Guide to understand the core
concepts, how to use the `flatten-tool` command and how to structure your own
data as spreadsheet sheets.

The Developer Guide (work in progress) will go into more detail about how
Flatten Tool works internally, how you can use it as a library and how you can
generate *source maps* that locate each value in a JSON document back to the
sheet and cell it came from in a source spreadsheet. Source maps are handy for
notifying users where they can go in their source spreadsheet to correct any
errors.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
