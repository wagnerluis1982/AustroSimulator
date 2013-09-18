from PySide.QtCore import Qt

from austro.simulator.cpu import Memory
from austro.ui.datamodel import DataItem, DataModel


class MemoryModel(DataModel):
    def __init__(self, memory, parent=None):
        assert isinstance(memory, Memory), "It's not a memory object"
        super(MemoryModel, self).__init__(["Addr.", "Data"], parent)

        self._rootItem.extend(
                [[n, memory.get_word(n)] for n in xrange(memory.size())])

    def data(self, index, role):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return super(MemoryModel, self).data(index, role)

    def setWord(self, address, data):
        index = self.index(address, 1)
        self.setData(index, data)
