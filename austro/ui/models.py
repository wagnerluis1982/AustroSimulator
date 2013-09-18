from PySide.QtCore import Qt

from austro.simulator.cpu import Memory, Registers
from austro.ui.datamodel import DataItem, DataModel


class GenRegsModel(DataModel):
    def __init__(self, registers, parent=None):
        assert isinstance(registers, Registers), "It's not a Registers object"
        super(GenRegsModel, self).__init__(("Name", "Data"), parent)

        self.registers = registers

        regAX = self.createItem('AX')
        regAX.appendChild(self.createItem('AH'))
        regAX.appendChild(self.createItem('AL'))
        self._rootItem.appendChild(regAX)

        regBX = self.createItem('BX')
        regBX.appendChild(self.createItem('BH'))
        regBX.appendChild(self.createItem('BL'))
        self._rootItem.appendChild(regBX)

        regCX = self.createItem('CX')
        regCX.appendChild(self.createItem('CH'))
        regCX.appendChild(self.createItem('CL'))
        self._rootItem.appendChild(regCX)

        regDX = self.createItem('DX')
        regDX.appendChild(self.createItem('DH'))
        regDX.appendChild(self.createItem('DL'))
        self._rootItem.appendChild(regDX)

        self._rootItem.appendChild(self.createItem('SP'))
        self._rootItem.appendChild(self.createItem('BP'))
        self._rootItem.appendChild(self.createItem('SI'))
        self._rootItem.appendChild(self.createItem('DI'))

    def createItem(self, name):
        item = (name, self.registers.get_reg(name))
        return DataItem(item)

    def data(self, index, role):
        if role == Qt.TextAlignmentRole and index.column() == 1:
            return Qt.AlignRight

        return super(GenRegsModel, self).data(index, role)


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
