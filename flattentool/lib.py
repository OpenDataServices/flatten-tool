from decimal import Decimal
# From http://bugs.python.org/issue16535
class NumberStr(float):
    def __init__(self, o):
        # We don't call the parent here, since we're deliberately altering it's functionality
        # pylint: disable=W0231
        self.o = o

    def __repr__(self):
        return str(self.o)

    # This is needed for this trick to work in python 3.4
    def __float__(self):
        return self

class Cell:
    __slots__ = ['cell_value', 'cell_location', 'sub_cells']
    def __init__(self, cell_value, cell_location):
        self.cell_value = cell_value
        self.cell_location = cell_location
        self.sub_cells = []

def decimal_default(o):
    if isinstance(o, Decimal):
        return NumberStr(o)
    if isinstance(o, Cell):
        return o.cell_value
    raise TypeError(repr(o) + " is not JSON serializable")
