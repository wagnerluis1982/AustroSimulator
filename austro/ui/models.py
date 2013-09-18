from PySide.QtCore import Qt

from austro.ui.datamodel import DataItem, DataModel


class MemoryModel(DataModel):
    def __init__(self, size, parent=None):
        super(MemoryModel, self).__init__(["Addr.", "Data"], parent)

        self._rootItem.extend([[addr, 0] for addr in xrange(size)])

    def data(self, index, role):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return super(MemoryModel, self).data(index, role)

    def setWord(self, address, data):
        index = self.index(address, 1)
        self.setData(index, data)
