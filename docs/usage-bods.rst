Flatten-Tool for BODS
+++++++++++++++++++++

flatten and unflatten
=====================

This data standard has a list as the root element,
as opposed to other standards where the root element is a dict with meta data and a list of data.
When flattening and unflattening, use the `--root-is-list` option.

The id element is `statementID`, so also use the `--id-name` option.

.. code-block:: bash

    flatten-tool flatten -f csv --root-is-list --id-name=statementID -o examples/bods-one-flatten examples/bods-one.json
    flatten-tool unflatten -f csv --root-is-list --id-name=statementID -o examples/bods-one-unflattened.json examples/bods-one-flatten


flatten
=======

This data standard has three types of statement - `entityStatement`, `personStatement` or `ownershipOrControlStatement`.
When using flatten, the spreadsheets produced can become very mixed up.

The main.csv spreadsheet will have data of all three types in it.
What's worse is that it's unclear what columns apply to what types -
for instance, `foundingDate` applies to entities but `birthDate` applies to people.
However both columns appear in main.csv!

It's also unclear what subsheets apply to which type - for instance there might be a subsheet called `identifiers`
but it's not clear what type this applies to! (The answer is entities)

It would be better to have separate sheets for each type.
That way, only the relevant columns will appear in each sheet and it will be clear which subsheet applies to which sheet.

You can solve this with a combination of the filter and sheet prefix options. To flatten a set of data, run 3 commands:

.. code-block:: bash

    flatten-tool flatten --sheet-prefix=1_person_ --filter-field=statementType --filter-value=personStatement -f csv -o example1/ example1.json --root-is-list --id-name=statementID
    flatten-tool flatten --sheet-prefix=2_entity_ --filter-field=statementType --filter-value=entityStatement -f csv -o example1/ example1.json --root-is-list --id-name=statementID
    flatten-tool flatten --sheet-prefix=3_ownership_ --filter-field=statementType --filter-value=ownershipOrControlStatement -f csv -o example1/ example1.json --root-is-list --id-name=statementID

You will have a set of sheets:

  *  1_person_addresses.csv
  *  1_person_main.csv
  *  1_person_names.csv
  *  1_person_nationalities.csv
  *  2_entity_identifiers.csv
  *  2_entity_main.csv
  *  3_ownership_interests.csv
  *  3_ownership_main.csv

`birthDate` only appears in `1_person_main.csv` and `foundingDate` only appears in `2_entity_main.csv`, so it is clear which column is for which type.

Note this works in csv mode.
If you want to use Excel mode, you'll need to specify 3 separate output files and then combine the sheets in them into one file afterwards by hand.

.. code-block:: bash

    flatten-tool flatten --sheet-prefix=1_person_ --filter-field=statementType --filter-value=personStatement -f xlsx -o example1/part1.xlsx example1.json --root-is-list --id-name=statementID
    flatten-tool flatten --sheet-prefix=2_entity_ --filter-field=statementType --filter-value=entityStatement -f xlsx -o example1/part2.xlsx example1.json --root-is-list --id-name=statementID
    flatten-tool flatten --sheet-prefix=3_ownership_ --filter-field=statementType --filter-value=ownershipOrControlStatement -f xlsx -o example1/part3.xlsx example1.json --root-is-list --id-name=statementID

unflatten
=========

Schema
------

As well as the options above, also pass the `--schema` option so that types are set correctly. Note the boolean and the integer in the output.

.. literalinclude:: ../examples/bods/unflatten/cmd.txt
   :language: bash

.. literalinclude:: ../examples/bods/unflatten/expected/out.json
   :language: json


Order is important
------------------

In the BODS schema, statements must appear in a certain order. Each of the `entityStatements` or `personStatements`
referenced by a particular `ownershipOrControlStatement` must appear before that particular statement in the ordered array.

If you have only one main table, you must make sure the statements appear in the correct order.

For example, this is good:

.. code-block:: csv

    statementID,statementType, ...
    1dc0e987-5c57-4a1c-b3ad-61353b66a9b7,entityStatement,
    019a93f1-e470-42e9-957b-03559861b2e2,personStatement,
    fbfd0547-d0c6-4a00-b559-5c5e91c34f5c,ownershipOrControlStatement,

Pay attention to other sheets to. If a subsheet is loaded before main.csv, the order might still be wrong.

Alternatively, you may have several main tables, one for each type of statement:

  *  main-control-own.csv
  *  main-entity.csv
  *  main-person.csv

In this case, you may get data in the wrong order.

To fix this, put numbers in front of the file names so that you can be sure what order they will appear in.
For instance:

  *  1identifiers.csv
  *  1main-entity.csv
  *  2addresses.csv
  *  2main-person.csv
  *  2names.csv
  *  2nationalities.csv
  *  3interests.csv
  *  3main-control-own.csv

create-template
===============

You can run this directly on `bods-package.json`:

.. code-block:: bash

    flatten-tool create-template -f csv -s bods-package.json -o template --root-id=statementID

However, this will produce spreadsheets where the several types are all mixed up. As explained above, this creates
problems because columns appear in the main sheet that are not relevant to all types, and it's not clear which subsheet applies to which type.

Instead, this process can be followed to obtain clearer templates:

1) Create a new blank directory and change into it.

2) Produce the person sheets only by running:

.. code-block:: bash

    flatten-tool  create-template -f csv -s /path/to/person-statement.json -o . --root-id=statementID

3) Rename all the files in the directory to have `1_person_` at the start.

If your on a bash shell, you can do this by running:

.. code-block:: bash

    for FILENAME in *; do mv $FILENAME 1_person_$FILENAME; done


4) Produce the entity sheets only by running:

.. code-block:: bash

    flatten-tool  create-template -f csv -s /path/to/entity-statement.json -o . --root-id=statementID


5) Rename all the new files in the directory to have `2_entity_` at the start.

If your on a bash shell, you can do this by running:

.. code-block:: bash

    for FILENAME in *; do if [[ $FILENAME != 1_* ]] ; then mv $FILENAME 2_entity_$FILENAME; fi; done



6) Produce the ownership or control sheets only by running:

.. code-block:: bash

    flatten-tool  create-template -f csv -s /path/to/ownership-or-control-statement.json -o . --root-id=statementID


7) Rename all the new files in the  directory to have `3_ownership_control_` at the start.

If your on a bash shell, you can do this by running:

.. code-block:: bash

    for FILENAME in *; do if [[ $FILENAME != 1_* ]] && [[ $FILENAME != 2_* ]] ; then mv $FILENAME 3_ownership_control_$FILENAME; fi; done

You will now have a directory of files that look like this:

  *  1_person_addresses.csv
  *  1_person_annotations.csv
  *  1_person_identifiers.csv
  *  1_person_main.csv
  *  1_person_names.csv
  *  1_person_nationalities.csv
  *  1_person_pepStatus.csv
  *  1_person_sou_assertedBy.csv
  *  2_entity_addresses.csv
  *  2_entity_annotations.csv
  *  2_entity_identifiers.csv
  *  2_entity_main.csv
  *  2_entity_sou_assertedBy.csv
  *  3_ownership_control_annotations.csv
  *  3_ownership_control_interests.csv
  *  3_ownership_control_main.csv
  *  3_ownership_control_sou_assertedBy.csv

The advantages are:

  *  Separate for each type, so it's clear what sheet applies to each type.
  *  Each sheet only has the relevant columns in it, so there is no confusion about whether they apply or not.
  *  The sheets have numbers at the start, so that when `unflatten` is used the statements will appear in the right order in the output.




