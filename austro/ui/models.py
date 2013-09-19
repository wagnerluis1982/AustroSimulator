from PySide.QtCore import Qt
from PySide.QtGui import QBrush, QColor

from austro.simulator.cpu import Memory, Registers
from austro.ui.datamodel import DataItem, DataModel


class RegistersModel(DataModel):
    def __init__(self, registers, items, parent=None):
        assert isinstance(registers, Registers), "It's not a Registers object"
        super(RegistersModel, self).__init__(("Name", "Data (%s)"), parent)
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
        super(MemoryModel, self).__init__(("Addr.", "Data (%s)"), parent)

        self.pc = -1  # invalid program counter

        for addr in xrange(memory.size()):
            item = (addr, memory.get_word(addr))
            self._rootItem.appendChild(DataItem(item))

    def data(self, index, role):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        elif role == Qt.BackgroundRole and self.pc >= 0 and \
                index.row() == self.pc:
            return QBrush(QColor("#C6DBAE"))

        return super(MemoryModel, self).data(index, role)
