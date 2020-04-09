# Copyright 2011 Marco Conti

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Thanks to grt for the fixes
# https://github.com/marcoconti83/read-ods-with-odfpy

import re
from collections import OrderedDict

import odf.opendocument
from odf.table import Table, TableCell, TableRow


# http://stackoverflow.com/a/4544699/1846474
class GrowingList(list):
    def __setitem__(self, index, value):
        if index >= len(self):
            self.extend([None] * (index + 1 - len(self)))
        list.__setitem__(self, index, value)


class ODSReader:

    # loads the file
    def __init__(self, file, clonespannedcolumns=None):
        self.clonespannedcolumns = clonespannedcolumns
        self.doc = odf.opendocument.load(file)
        self.SHEETS = OrderedDict()
        for sheet in self.doc.spreadsheet.getElementsByType(Table):
            self.readSheet(sheet)

    # reads a sheet in the sheet dictionary, storing each sheet as an
    # array (rows) of arrays (columns)
    def readSheet(self, sheet):
        name = sheet.getAttribute("name")
        rows = sheet.getElementsByType(TableRow)
        arrRows = []

        # for each row
        for row in rows:
            row_comment = ""  # noqa
            arrCells = GrowingList()
            cells = row.getElementsByType(TableCell)

            # for each cell
            count = 0
            for cell in cells:
                # repeated value?
                repeat = cell.getAttribute("numbercolumnsrepeated")
                if not repeat:
                    repeat = 1
                    spanned = int(cell.getAttribute("numbercolumnsspanned") or 0)
                    # clone spanned cells
                    if self.clonespannedcolumns is not None and spanned > 1:
                        repeat = spanned

                for rr in range(int(repeat)):  # repeated?
                    if str(cell):
                        value_type = cell.attributes.get(
                            (
                                "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
                                "value-type",
                            )
                        )
                        if value_type == "float":
                            if "." in str(cell):
                                arrCells[count] = float(str(cell))
                            else:
                                arrCells[count] = int(str(cell))
                        elif value_type == "date":
                            date_value = cell.attributes.get(
                                (
                                    "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
                                    "date-value",
                                )
                            )
                            # Add UTC timezone to naive datetime strings
                            if re.match(
                                r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$", date_value
                            ):
                                date_value += "Z"
                            arrCells[count] = date_value
                        else:
                            arrCells[count] = str(cell)
                    count += 1

            arrRows.append(arrCells)

        self.SHEETS[name] = arrRows

    # returns a sheet as an array (rows) of arrays (columns)
    def getSheet(self, name):
        return self.SHEETS[name]
