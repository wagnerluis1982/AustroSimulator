from PySide.QtCore import QAbstractItemModel, QModelIndex, Qt


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
    F_DEC_TWO = 0

    FORMATS = {
            F_BIN: "0b{0:b}",
            F_OCT: "0{0:o}",
            F_HEX: "0x{0:x}",
        }

    def __init__(self, header, parent=None):
        super(DataModel, self).__init__(parent)

        self._rootItem = DataItem(header)
        self.setDataFormat(self.F_DEC)

    def setDataFormat(self, noFormat):
        self._fmt = noFormat
        self.refresh()

    def format(self, data):
        if self._fmt in (DataModel.F_DEC, DataModel.F_DEC_TWO):
            return data
        elif self._fmt == DataModel.F_OCT and data == 0:
            return 0

        return str.format(DataModel.FORMATS[self._fmt], data)

    def index(self, row, column, parent=QModelIndex()):
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
            return self.format(item.data(column))

        return item.data(column)

    def flags(self, index):
        if not index.isValid():
            return 0

        return Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._rootItem.data(section)

        return None

    def refresh(self):
        first = self.index(0, 0)
        last = self.index(self.rowCount()-1, self.columnCount()-1)
        self.dataChanged.emit(first, last)
