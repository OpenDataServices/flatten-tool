import copy

import BTrees.IOBTree


class Sheet(object):
    """
    An abstract representation of a single sheet of a spreadsheet.

    """

    def __init__(self, columns=None, root_id="", name=None):
        self.id_columns = []
        self.columns = columns if columns else []
        self.titles = {}
        self._lines = []
        self.root_id = root_id
        self.name = name

    @property
    def lines(self):
        return self._lines

    def add_field(self, field, id_field=False):
        columns = self.id_columns if id_field else self.columns
        if field not in columns:
            columns.append(field)

    def append(self, item):
        self.add_field(item)

    def __iter__(self):
        if self.root_id:
            yield self.root_id
        for column in self.id_columns:
            yield column
        for column in self.columns:
            yield column

    def append_line(self, flattened_dict):
        self._lines.append(flattened_dict)


class PersistentSheet(Sheet):
    """
    A sheet that is persisted in ZODB database.

    """

    def __init__(self, columns=None, root_id="", name=None, connection=None):
        super().__init__(columns=columns, root_id=root_id, name=name)
        self.connection = connection
        self.index = 0
        # Integer key and object value btree.  Store sequential index in order to preserve input order.
        connection.root.sheet_store[self.name] = BTrees.IOBTree.BTree()

    @property
    def lines(self):
        # btrees iterate in key order.
        for key, value in self.connection.root.sheet_store[self.name].items():
            # 5000 chosen by trial and error.  The written row
            # data is removed from memory as is no loner needed.
            # All new sheets clear out previous sheets data from memory.
            if key % 5000 == 0:
                self.connection.cacheMinimize()
            yield value

    def append_line(self, flattened_dict):
        self.connection.root.sheet_store[self.name][self.index] = flattened_dict
        self.index += 1

    @classmethod
    def from_sheet(cls, sheet, connection):
        instance = cls(name=sheet.name, connection=connection)
        instance.id_columns = copy.deepcopy(sheet.id_columns)
        instance.columns = copy.deepcopy(sheet.columns)
        instance.titles = copy.deepcopy(sheet.titles)
        instance.root_id = sheet.root_id
        return instance
