class Sheet(object):
    """
    An abstract representation of a single sheet of a spreadsheet.

    """

    def __init__(self, columns=None, root_id='', name=None):
        self.id_columns = []
        self.columns = columns if columns else []
        self.titles = {}
        self.lines = []
        self.root_id = root_id
        self.name = name

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
