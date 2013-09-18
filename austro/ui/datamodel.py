from PySide.QtCore import QAbstractItemModel, QModelIndex, Qt


class DataItem(object):
    def __init__(self, data, parent=None):
        self._parentItem = parent
        self._itemData = data
        self._childItems = []

    def append(self, item):
        self._childItems.append(DataItem(item, self))

    def extend(self, items):
        self._childItems.extend([DataItem(item, self) for item in items])

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

    def setData(self, column, value):
        self._itemData[column] = value

    def row(self):
        if self._parentItem:
            return self._parentItem._childItems.index(self)

        return 0

    def parent(self):
        return self._parentItem


class DataModel(QAbstractItemModel):
    def __init__(self, header, parent=None):
        super(DataModel, self).__init__(parent)

        self._rootItem = DataItem(header)

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
            parentItem = parentItem.internalPointer()

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

        return item.data(index.column())

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            index.internalPointer().setData(column, value)
            self.dataChanged.emit(index, index)
            return True

        return super(DataModel, self).setData(index, value, role)

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
