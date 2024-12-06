Getting Started
===============

Prerequisites
-------------

You will need Python 3.6 or later, including the venv module.

Generally the venv module should come with your default Python install, but not on Ubuntu.  On Ubuntu run:

.. code-block:: bash

   sudo apt-get install python3 python3-venv

Installation
------------

.. code-block:: bash

    git clone https://github.com/OpenDataServices/flatten-tool.git
    cd flatten-tool
    python3 -m venv .ve
    source .ve/bin/activate
    pip install -r requirements_dev.txt

Usage
-----

.. code-block:: bash

    flatten-tool -h

will print general help information.

.. code-block:: bash

    flatten-tool {create-template,flatten,unflatten} -h

will print help information specific to that sub-command.

Library
-------

The package can also be used as a Python library, e.g. to flatten
data:

.. code-block:: python

    flattentool.flatten(input_filename, ...)

or unflatten data:

.. code-block:: python

    flattentool.unflatten(input_filename, ...)

In addition to the functionality available from the command-line, 
Python calls to the library functions also accept a Python object
as a schema rather than a filename. This allows schema objects to
be loaded/constructed by the calling application.

Python Version Support
----------------------

This code supports Python 3.9 (and later).

Earlier versions (including Python 2) are not supported, because they are
end of life, and some of the dependencies do not support them.
