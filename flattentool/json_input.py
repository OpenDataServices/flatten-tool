"""

This file contains code that takes an instance of a JSON file as input (not a
JSON schema, for that see schema.py).

"""

import codecs
import copy
import os
import tempfile
import uuid
from collections import OrderedDict
from decimal import Decimal
from warnings import warn

import BTrees.OOBTree
import ijson
import transaction
import xmltodict
import zc.zlibstorage
import ZODB.FileStorage

from flattentool.i18n import _
from flattentool.input import path_search
from flattentool.schema import make_sub_sheet_name
from flattentool.sheet import PersistentSheet

BASIC_TYPES = [str, bool, int, Decimal, type(None)]


class BadlyFormedJSONError(ValueError):
    pass


class BadlyFormedJSONErrorUTF8(BadlyFormedJSONError):
    pass


def sheet_key_field(sheet, key):
    if key not in sheet:
        sheet.append(key)
    return key


def sheet_key_title(sheet, key):
    """
    If the key has a corresponding title, return that. If doesn't, create it in the sheet and return it.

    """
    if key in sheet.titles:
        title = sheet.titles[key]
        if title not in sheet:
            sheet.append(title)
        return title
    else:
        if key not in sheet:
            sheet.append(key)
        return key


def lists_of_dicts_paths(xml_dict):
    for key, value in xml_dict.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            yield (key,)
            for x in value:
                if isinstance(x, dict):
                    for path in lists_of_dicts_paths(x):
                        yield (key,) + path
        elif isinstance(value, dict):
            for path in lists_of_dicts_paths(value):
                yield (key,) + path


def dicts_to_list_of_dicts(lists_of_dicts_paths_set, xml_dict, path=()):
    for key, value in xml_dict.items():
        if isinstance(value, list):
            for x in value:
                if isinstance(x, dict):
                    dicts_to_list_of_dicts(lists_of_dicts_paths_set, x, path + (key,))
        elif isinstance(value, dict):
            child_path = path + (key,)
            dicts_to_list_of_dicts(lists_of_dicts_paths_set, value, child_path)
            if child_path in lists_of_dicts_paths_set:
                xml_dict[key] = [value]


def list_dict_consistency(xml_dict):
    """
    For use with XML files opened with xmltodict.

    If there is only one tag, xmltodict produces a dict. If there are
    multiple, xmltodict produces a list of dicts. This functions replaces
    dicts with lists of dicts, if there exists a list of dicts for the same
    path elsewhere in the file.
    """
    lists_of_dicts_paths_set = set(lists_of_dicts_paths(xml_dict))
    dicts_to_list_of_dicts(lists_of_dicts_paths_set, xml_dict)


class JSONParser(object):
    # Named for consistency with schema.SchemaParser, but not sure it's the most appropriate name.
    # Similarly with methods like parse_json_dict

    def __init__(
        self,
        json_filename=None,
        root_json_dict=None,
        schema_parser=None,
        root_list_path=None,
        root_id="ocid",
        use_titles=False,
        xml=False,
        id_name="id",
        filter_field=None,
        filter_value=None,
        preserve_fields=None,
        remove_empty_schema_columns=False,
        rollup=False,
        truncation_length=3,
        persist=False,
    ):
        if persist:
            # Use temp directories in OS agnostic way
            self.zodb_db_location = (
                tempfile.gettempdir() + "/flattentool-" + str(uuid.uuid4())
            )
            # zlibstorage lowers disk usage by a lot at very small performance cost
            zodb_storage = zc.zlibstorage.ZlibStorage(
                ZODB.FileStorage.FileStorage(self.zodb_db_location)
            )
            self.db = ZODB.DB(zodb_storage)
        else:
            # If None, in memory storage is used.
            self.db = ZODB.DB(None)

        self.connection = self.db.open()

        # ZODB root, only objects attached here will be persisted
        root = self.connection.root
        # OOBTree means a btree with keys and values are objects (including strings)
        root.sheet_store = BTrees.OOBTree.BTree()

        self.sub_sheets = {}
        self.main_sheet = PersistentSheet(connection=self.connection, name="")
        self.root_list_path = root_list_path
        self.root_id = root_id
        self.use_titles = use_titles
        self.truncation_length = truncation_length
        self.id_name = id_name
        self.xml = xml
        self.filter_field = filter_field
        self.filter_value = filter_value
        self.remove_empty_schema_columns = remove_empty_schema_columns
        self.seen_paths = set()
        self.persist = persist

        if schema_parser:
            # schema parser does not make sheets that are persistent,
            # so use from_sheets which deep copies everything in it.
            self.main_sheet = PersistentSheet.from_sheet(
                schema_parser.main_sheet, self.connection
            )
            for sheet_name, sheet in list(self.sub_sheets.items()):
                self.sub_sheets[sheet_name] = PersistentSheet.from_sheet(
                    sheet, self.connection
                )

            self.sub_sheets = copy.deepcopy(schema_parser.sub_sheets)
            if remove_empty_schema_columns:
                # Don't use columns from the schema parser
                # (avoids empty columns)
                self.main_sheet.columns = []
                for sheet_name, sheet in list(self.sub_sheets.items()):
                    sheet.columns = []
            self.schema_parser = schema_parser
        else:
            self.schema_parser = None

        self.rollup = False
        if rollup:
            if schema_parser and len(schema_parser.rollup) > 0:
                # If rollUp is present in the schema this takes precedence over direct input.
                self.rollup = schema_parser.rollup
                if isinstance(rollup, (list,)) and (
                    len(rollup) > 1 or (len(rollup) == 1 and rollup[0] is not True)
                ):
                    warn(_("Using rollUp values from schema, ignoring direct input."))
            elif isinstance(rollup, (list,)):
                if len(rollup) == 1 and os.path.isfile(rollup[0]):
                    # Parse file, one json path per line.
                    rollup_from_file = set()
                    with open(rollup[0]) as rollup_file:
                        for line in rollup_file:
                            line = line.strip()
                            rollup_from_file.add(line)
                    self.rollup = rollup_from_file
                    # Rollup args passed directly at the commandline
                elif len(rollup) == 1 and rollup[0] is True:
                    warn(
                        _(
                            "No fields to rollup found (pass json path directly, as a list in a file, or via a schema)"
                        )
                    )
                else:
                    self.rollup = set(rollup)
            else:
                warn(
                    _(
                        "Invalid value passed for rollup (pass json path directly, as a list in a file, or via a schema)"
                    )
                )

        if self.xml:
            with codecs.open(json_filename, "rb") as xml_file:
                top_dict = xmltodict.parse(
                    xml_file,
                    force_list=(root_list_path,),
                    force_cdata=True,
                )
                # AFAICT, this should be true for *all* XML files
                assert len(top_dict) == 1
                root_json_dict = list(top_dict.values())[0]
                list_dict_consistency(root_json_dict)
            json_filename = None

        if json_filename is None and root_json_dict is None:
            raise ValueError(
                _("Either json_filename or root_json_dict must be supplied")
            )

        if json_filename is not None and root_json_dict is not None:
            raise ValueError(
                _("Only one of json_file or root_json_dict should be supplied")
            )

        if not json_filename:
            if self.root_list_path is None:
                self.root_json_list = root_json_dict
            else:
                self.root_json_list = path_search(
                    root_json_dict, self.root_list_path.split("/")
                )

        if preserve_fields:
            # Extract fields to be preserved from input file (one path per line)
            preserve_fields_all = []
            preserve_fields_input = []
            with open(preserve_fields) as preserve_fields_file:
                for line in preserve_fields_file:
                    line = line.strip()
                    path_fields = line.rsplit("/", 1)
                    preserve_fields_all = (
                        preserve_fields_all + path_fields + [line.rstrip("/")]
                    )
                    preserve_fields_input = preserve_fields_input + [line.rstrip("/")]

            self.preserve_fields = set(preserve_fields_all)
            self.preserve_fields_input = set(preserve_fields_input)

            try:
                input_not_in_schema = set()
                for field in self.preserve_fields_input:
                    if field not in self.schema_parser.flattened.keys():
                        input_not_in_schema.add(field)
                warn(
                    _(
                        "You wanted to preserve the following fields which are not present in the supplied schema: {}"
                    ).format(list(input_not_in_schema))
                )
            except AttributeError:
                # no schema
                pass
        else:
            self.preserve_fields = None
            self.preserve_fields_input = None

        if json_filename:
            if self.root_list_path is None:
                path = "item"
            else:
                path = root_list_path.replace("/", ".") + ".item"

            json_file = codecs.open(json_filename, encoding="utf-8")

            self.root_json_list = ijson.items(json_file, path, map_type=OrderedDict)

        try:
            self.parse()
        except ijson.common.IncompleteJSONError as err:
            raise BadlyFormedJSONError(*err.args)
        except UnicodeDecodeError as err:
            raise BadlyFormedJSONErrorUTF8(*err.args)
        finally:
            if json_filename:
                json_file.close()

    def parse(self):
        for num, json_dict in enumerate(self.root_json_list):
            if json_dict is None:
                # This is particularly useful for IATI XML, in order to not
                # fall over on empty activity, e.g. <iati-activity/>
                continue
            self.parse_json_dict(json_dict, sheet=self.main_sheet)
            # only persist every 2000 objects. peristing more often slows down storing.
            # 2000 top level objects normally not too much to store in memory.
            if num % 2000 == 0 and num != 0:
                transaction.commit()

        # This commit could be removed which would mean that upto 2000 objects
        # could be stored in memory without anything being persisted.
        transaction.commit()

        if self.remove_empty_schema_columns:
            # Remove sheets with no lines of data
            for sheet_name, sheet in list(self.sub_sheets.items()):
                if not sheet.lines:
                    del self.sub_sheets[sheet_name]

        if self.preserve_fields_input:
            nonexistent_input_paths = []
            for field in self.preserve_fields_input:
                if field not in self.seen_paths:
                    nonexistent_input_paths.append(field)
            if len(nonexistent_input_paths) > 0:
                warn(
                    _(
                        "You wanted to preserve the following fields which are not present in the input data: {}"
                    ).format(nonexistent_input_paths)
                )

    def parse_json_dict(
        self,
        json_dict,
        sheet,
        json_key=None,
        parent_name="",
        flattened_dict=None,
        parent_id_fields=None,
        top_level_of_sub_sheet=False,
    ):
        """
        Parse a json dictionary.

        json_dict - the json dictionary
        sheet - a sheet.Sheet object representing the resulting spreadsheet
        json_key - the key that maps to this JSON dict, either directly to the dict, or to a dict that this list contains.  Is None if this dict is contained in root_json_list directly.
        """
        # Possibly main_sheet should be main_sheet_columns, but this is
        # currently named for consistency with schema.py

        if self.use_titles:
            sheet_key = sheet_key_title
        else:
            sheet_key = sheet_key_field

        parent_id_fields = copy.copy(parent_id_fields) or OrderedDict()
        if flattened_dict is None:
            flattened_dict = {}
            top = True
        else:
            top = False

        if parent_name == "" and self.filter_field and self.filter_value:
            if self.filter_field not in json_dict:
                return
            if json_dict[self.filter_field] != self.filter_value:
                return

        if top_level_of_sub_sheet:
            # Add the IDs for the top level of object in an array
            for k, v in parent_id_fields.items():
                if self.xml:
                    flattened_dict[sheet_key(sheet, k)] = v["#text"]
                else:
                    flattened_dict[sheet_key(sheet, k)] = v

        if self.root_id and self.root_id in json_dict:
            parent_id_fields[sheet_key(sheet, self.root_id)] = json_dict[self.root_id]

        if self.id_name in json_dict:
            parent_id_fields[sheet_key(sheet, parent_name + self.id_name)] = json_dict[
                self.id_name
            ]

        for key, value in json_dict.items():

            # Keep a unique list of all the JSON paths in the data that have been seen.
            parent_path = parent_name.replace("/0", "")
            full_path = parent_path + key
            self.seen_paths.add(full_path)

            if self.preserve_fields:

                siblings = False
                for field in self.preserve_fields:
                    if parent_path in field:
                        siblings = True
                if siblings and full_path not in self.preserve_fields:
                    continue

            if type(value) in BASIC_TYPES:
                if self.xml and key == "#text":
                    # Handle the text output from xmltodict
                    key = ""
                    parent_name = parent_name.strip("/")
                flattened_dict[sheet_key(sheet, parent_name + key)] = value
            elif hasattr(value, "items"):
                self.parse_json_dict(
                    value,
                    sheet=sheet,
                    json_key=key,
                    parent_name=parent_name + key + "/",
                    flattened_dict=flattened_dict,
                    parent_id_fields=parent_id_fields,
                )
            elif hasattr(value, "__iter__"):
                if all(type(x) in BASIC_TYPES for x in value):
                    # Check for an array of BASIC types
                    # TODO Make this check the schema
                    # TODO Error if the any of the values contain the separator
                    flattened_dict[sheet_key(sheet, parent_name + key)] = ";".join(
                        map(str, value)
                    )
                # Arrays of arrays
                elif all(
                    l not in BASIC_TYPES
                    and not hasattr(l, "items")
                    and hasattr(l, "__iter__")
                    and all(type(x) in BASIC_TYPES for x in l)
                    for l in value
                ):
                    flattened_dict[sheet_key(sheet, parent_name + key)] = ";".join(
                        map(lambda l: ",".join(map(str, l)), value)
                    )
                else:
                    if (
                        self.rollup and parent_name == ""
                    ):  # Rollup only currently possible to main sheet

                        if self.use_titles and not self.schema_parser:
                            warn(
                                _(
                                    "Warning: No schema was provided so column headings are JSON keys, not titles."
                                )
                            )

                        if len(value) == 1:
                            for k, v in value[0].items():

                                if (
                                    self.preserve_fields
                                    and parent_name + key + "/" + k
                                    not in self.preserve_fields
                                ):
                                    continue

                                if type(v) not in BASIC_TYPES:
                                    raise ValueError(
                                        _("Rolled up values must be basic types")
                                    )
                                else:
                                    if self.schema_parser:
                                        # We want titles and there's a schema and rollUp is in it
                                        if (
                                            self.use_titles
                                            and parent_name + key + "/0/" + k
                                            in self.schema_parser.main_sheet.titles
                                        ):
                                            flattened_dict[
                                                sheet_key_title(
                                                    sheet, parent_name + key + "/0/" + k
                                                )
                                            ] = v

                                        # We want titles and there's a schema but rollUp isn't in it
                                        # so the titles for rollup properties aren't in the main sheet
                                        # so we need to try to get the titles from a subsheet
                                        elif (
                                            self.use_titles
                                            and parent_name + key in self.rollup
                                            and self.schema_parser.sub_sheet_titles.get(
                                                (
                                                    parent_name,
                                                    key,
                                                )
                                            )
                                            in self.schema_parser.sub_sheets
                                        ):
                                            relevant_subsheet = self.schema_parser.sub_sheets.get(
                                                self.schema_parser.sub_sheet_titles.get(
                                                    (
                                                        parent_name,
                                                        key,
                                                    )
                                                )
                                            )
                                            if relevant_subsheet is not None:
                                                rollup_field_title = sheet_key_title(
                                                    relevant_subsheet,
                                                    parent_name + key + "/0/" + k,
                                                )
                                                flattened_dict[
                                                    sheet_key(sheet, rollup_field_title)
                                                ] = v

                                        # We don't want titles even though there's a schema
                                        elif not self.use_titles and (
                                            parent_name + key + "/0/" + k
                                            in self.schema_parser.main_sheet
                                            or parent_name + key in self.rollup
                                        ):
                                            flattened_dict[
                                                sheet_key(
                                                    sheet, parent_name + key + "/0/" + k
                                                )
                                            ] = v

                                    # No schema, so no titles
                                    elif parent_name + key in self.rollup:
                                        flattened_dict[
                                            sheet_key(
                                                sheet, parent_name + key + "/0/" + k
                                            )
                                        ] = v

                        elif len(value) > 1:
                            for k in set(sum((list(x.keys()) for x in value), [])):

                                if (
                                    self.preserve_fields
                                    and parent_name + key + "/" + k
                                    not in self.preserve_fields
                                ):
                                    continue

                                if (
                                    self.schema_parser
                                    and parent_name + key + "/0/" + k
                                    in self.schema_parser.main_sheet
                                ):
                                    warn(
                                        _(
                                            'More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'
                                        ).format(parent_name + key)
                                    )
                                    flattened_dict[
                                        sheet_key(sheet, parent_name + key + "/0/" + k)
                                    ] = _(
                                        "WARNING: More than one value supplied, consult the relevant sub-sheet for the data."
                                    )
                                elif parent_name + key in self.rollup:
                                    warn(
                                        _(
                                            'More than one value supplied for "{}". Could not provide rollup, so adding a warning to the relevant cell(s) in the spreadsheet.'
                                        ).format(parent_name + key)
                                    )
                                    flattened_dict[
                                        sheet_key(sheet, parent_name + key + "/0/" + k)
                                    ] = _(
                                        "WARNING: More than one value supplied, consult the relevant sub-sheet for the data."
                                    )

                    if (
                        self.use_titles
                        and self.schema_parser
                        and (
                            parent_name,
                            key,
                        )
                        in self.schema_parser.sub_sheet_titles
                    ):
                        sub_sheet_name = self.schema_parser.sub_sheet_titles[
                            (
                                parent_name,
                                key,
                            )
                        ]
                    else:
                        sub_sheet_name = make_sub_sheet_name(
                            parent_name, key, truncation_length=self.truncation_length
                        )
                    if sub_sheet_name not in self.sub_sheets:
                        self.sub_sheets[sub_sheet_name] = PersistentSheet(
                            name=sub_sheet_name, connection=self.connection
                        )

                    for json_dict in value:
                        if json_dict is None:
                            continue
                        self.parse_json_dict(
                            json_dict,
                            sheet=self.sub_sheets[sub_sheet_name],
                            json_key=key,
                            parent_id_fields=parent_id_fields,
                            parent_name=parent_name + key + "/0/",
                            top_level_of_sub_sheet=True,
                        )
            else:
                raise ValueError(_("Unsupported type {}").format(type(value)))

        if top:
            sheet.append_line(flattened_dict)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.persist:
            self.connection.close()
            self.db.close()
            os.remove(self.zodb_db_location)
            os.remove(self.zodb_db_location + ".lock")
            os.remove(self.zodb_db_location + ".index")
            os.remove(self.zodb_db_location + ".tmp")
