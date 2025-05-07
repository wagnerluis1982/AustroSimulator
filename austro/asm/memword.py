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

from austro.shared import AbstractData


class Word(AbstractData, ctypes.Structure):
    '''Represent the memory word

    Word objects can act as instruction or data words of 16 bits
    '''

    _fields_ = (
        ("_opcode", ctypes.c_ubyte, 5),
        ("_flags", ctypes.c_ubyte, 3),
        ("_operand", ctypes.c_ubyte, 8),
        ("_value", ctypes.c_uint16),
    )
    _bits = 16

    def __init__(self, opcode=0, flags=0, operand=0, lineno=0, value=None, is_instruction=False):
        # Flag to know if this word should act as a instruction
        self._instruction = is_instruction
        # Set an associated assembly code line number (for instructions)
        self.lineno = lineno

        # If marked as instruction, set args separately
        if is_instruction:
            ctypes.Structure.__init__(self, opcode, flags, operand)

        # In a data word the 'value' must be set
        else:
            assert value is not None, "DWord requires 'value' but was not set"
            self.value = value

    @property
    def value(self):
        if self.is_instruction:
            return (self.opcode << 3 | self.flags) << 8 | self.operand
        else:
            return self._value

    @value.setter
    def value(self, value):
        if self.is_instruction:
            self.opcode = value >> 11
            self.flags = value >> 8
            self.operand = value
        else:
            self._value = value

    @property
    def opcode(self):
        assert self.is_instruction, "Word is not a instruction"
        return self._opcode

    @opcode.setter
    def opcode(self, value):
        assert self.is_instruction, "Word is not a instruction"
        self._opcode = value

    @property
    def flags(self):
        assert self.is_instruction, "Word is not a instruction"
        return self._flags

    @flags.setter
    def flags(self, value):
        assert self.is_instruction, "Word is not a instruction"
        self._flags = value

    @property
    def operand(self):
        assert self.is_instruction, "Word is not a instruction"
        return self._operand

    @operand.setter
    def operand(self, value):
        assert self.is_instruction, "Word is not a instruction"
        self._operand = value

    @property
    def is_instruction(self):
        return self._instruction

    @is_instruction.setter
    def is_instruction(self, switch):
        if switch:
            if not self._instruction:
                self._instruction = True
                self.value = self._value
        else:
            if self._instruction:
                value = self.value
                self._instruction = False
                self.value = value

    def __eq__(self, o):
        return self.value == o.value

    def __repr__(self):
        if self.is_instruction:
            return f"IWord({self.opcode}, {self.flags}, {self.operand}, lineno={self.lineno})"
        else:
            return f"DWord({self._value})"


def IWord(opcode=0, flags=0, operand=0, lineno=0) -> Word:
    """Helper to create an Instruction Word"""
    return Word(opcode, flags, operand, lineno, is_instruction=True)


def DWord(value=0):
    """Helper to create a Data Word"""
    return Word(value=value)
