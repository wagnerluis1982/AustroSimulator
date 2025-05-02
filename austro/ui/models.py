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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor

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


# Model for memory data vision
class MemoryModel(DataModel):
    def __init__(self, memory, parent=None):
        assert isinstance(memory, Memory), "It's not a memory object"
        super(MemoryModel, self).__init__(("Addr.", "Data (%s)"), parent)

        for addr in range(memory.size()):
            item = (addr, memory.get_word(addr))
            self._rootItem.appendChild(DataItem(item))

    def data(self, index, role):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return super(MemoryModel, self).data(index, role)


# Model for memory general vision
class GeneralMemoryModel(MemoryModel):
    # New format option
    F_INSTR = 5

    def __init__(self, memory, parent=None):
        super(GeneralMemoryModel, self).__init__(memory, parent)

        # Invalid program counter
        self.pc = -1

        # Create reverse OPCODES mapping
        from austro.asm.assembler import OPCODES
        self.OPCODES = dict([(code, name) for name, code in OPCODES.items()
                if name not in ('IMUL', 'IDIV', 'IMOD', 'ICMP')])

    def data(self, index, role):
        if role == Qt.BackgroundRole and self.pc >= 0 and \
                index.row() == self.pc:
            return QBrush(QColor("#C6DBAE"))

        if self._fmt == self.F_INSTR and role == Qt.DisplayRole and \
                index.isValid() and index.column() == 1:
            word = index.internalPointer()._itemData[1]
            if word.is_instruction:
                return self.OPCODES[word.opcode]

        return super(GeneralMemoryModel, self).data(index, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if self._fmt == self.F_INSTR and orientation == Qt.Horizontal and \
                role == Qt.DisplayRole and section == 1:
            header = self._rootItem.data(section)
            return header % 'INSTR.'

        return super(GeneralMemoryModel, self).headerData(section, orientation,
                role)
