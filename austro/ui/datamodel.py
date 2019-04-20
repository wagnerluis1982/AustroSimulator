# Copyright (C) 2013  Wagner Macedo <wagnerluis1982@gmail.com>
#
# This file is part of Austro Simulator.
#
# Austro Simulator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Austro Simulator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Austro Simulator.  If not, see <http://www.gnu.org/licenses/>.

import ctypes

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt


class DataItem(object):
    def __init__(self, data, parent=None):
        self._parentItem = parent
        self._itemData = data
        self._childItems = []

    def appendChild(self, item):
        item._parentItem = self
        self._childItems.append(item)

    def child(self, row):
        return self._childItems[row]

    def childCount(self):
        return len(self._childItems)

    def columnCount(self):
        return len(self._itemData)

    def bits(self):
        if self.parent() != None:
            return self._itemData[1].bits

    def data(self, column):
        if self.parent() != None and column == 1:
            return self._itemData[column].value

        return self._itemData[column]

    def row(self):
        if self._parentItem:
            return self._parentItem._childItems.index(self)

        return 0

    def parent(self):
        return self._parentItem


class DataModel(QAbstractItemModel):
    # Format options
    F_BIN = 2
    F_OCT = 8
    F_DEC = 10
    F_HEX = 16
    F_DEC_NEG = 0

    FMT_HEADER = {
            F_BIN: 'BIN',
            F_OCT: 'OCT',
            F_DEC: 'DEC',
            F_HEX: 'HEX',
            F_DEC_NEG: 'NEG',
        }

    def __init__(self, header, parent=None):
        super(DataModel, self).__init__(parent)

        self._rootItem = DataItem(header)
        self.setDataFormat(self.F_DEC)

    def setDataFormat(self, noFormat):
        self._fmt = noFormat
        self.headerDataChanged.emit(Qt.Horizontal, 1, 1)
        self.refresh()

    def format(self, data, bits):
        if self._fmt == DataModel.F_DEC_NEG:
            if bits == 8:
                return ctypes.c_int8(data).value
            elif bits == 16:
                return ctypes.c_int16(data).value
        elif self._fmt == DataModel.F_BIN:
            return str.format("0b{0:0%db}" % bits, data)
        elif self._fmt == DataModel.F_HEX:
            return str.format("0x{0:0%dx}" % (bits//4), data)
        elif self._fmt == DataModel.F_OCT:
            return str.format("0o{0:0%do}" % (bits//3), data)

        return data

    def index(self, row, column=0, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self._rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()
        column = index.column()
        if column == 1:
            return self.format(item.data(column), item.bits())

        return item.data(column)

    def flags(self, index):
        if not index.isValid():
            return 0

        return Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return self._rootItem.data(section)
            else:
                header = self._rootItem.data(section)
                return header % DataModel.FMT_HEADER[self._fmt]

        return None

    def refresh(self):
        first = self.index(0, 0)
        last = self.index(self.rowCount()-1, self.columnCount()-1)
        self.dataChanged.emit(first, last)
