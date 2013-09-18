from PySide.QtCore import Qt

from austro.simulator.cpu import Memory, Registers
from austro.ui.datamodel import DataItem, DataModel


class RegistersModel(DataModel):
    def __init__(self, registers, items, parent=None):
        assert isinstance(registers, Registers), "It's not a Registers object"
        super(RegistersModel, self).__init__(("Name", "Data"), parent)
        self.registers = registers

        dataItem = DataItem([])
        for item in items:
            if isinstance(item, (tuple, list)):
                for subItem in item:
                    dataItem.appendChild(self.createItem(subItem))
            else:
                dataItem = self.createItem(item)
                self._rootItem.appendChild(dataItem)

    def createItem(self, name):
        item = (name, self.registers.get_reg(name))
        return DataItem(item)

    def data(self, index, role):
        if role == Qt.TextAlignmentRole and index.column() == 1:
            return Qt.AlignRight

        return super(RegistersModel, self).data(index, role)


class MemoryModel(DataModel):
    def __init__(self, memory, parent=None):
        assert isinstance(memory, Memory), "It's not a memory object"
        super(MemoryModel, self).__init__(("Addr.", "Data"), parent)

        for addr in xrange(memory.size()):
            item = (addr, memory.get_word(addr))
            self._rootItem.appendChild(DataItem(item))

    def data(self, index, role):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return super(MemoryModel, self).data(index, role)
