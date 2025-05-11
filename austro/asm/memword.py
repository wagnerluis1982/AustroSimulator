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
from __future__ import annotations

import ctypes

from austro.shared import BaseData


class Word(BaseData):
    """Represent the memory word

    Word objects can act as instruction or data words of 16 bits
    """

    bits = 16

    def __init__(
        self, opcode=0, flags=0, operand=0, lineno=0, value=None, is_instruction=False
    ):
        self._opcode = ctypes.c_ubyte(opcode)
        self._flags = ctypes.c_ubyte(flags)
        self._operand = ctypes.c_ubyte(operand)
        self._value = ctypes.c_uint16()

        # Flag to know if this word should act as an instruction
        self._instruction = is_instruction
        # Set an associated assembly code line number (for instructions)
        self.lineno = lineno

        # In a data word the 'value' must be set
        if not is_instruction:
            assert value is not None, "DWord requires 'value' but was not set"
            self._value.value = value

    @property
    def value(self) -> int:
        if self.is_instruction:
            return (self.opcode << 3 | self.flags) << 8 | self.operand
        else:
            return self._value.value

    @value.setter
    def value(self, value: int) -> None:
        if self.is_instruction:
            self.opcode = value >> 11
            self.flags = (value >> 8) & 0b111
            self.operand = value & 0xFFFF
        else:
            self._value.value = value

    @property
    def opcode(self) -> int:
        assert self.is_instruction, "Word is not an instruction"
        return self._opcode.value

    @opcode.setter
    def opcode(self, value: int) -> None:
        assert self.is_instruction, "Word is not an instruction"
        self._opcode.value = value

    @property
    def flags(self) -> int:
        assert self.is_instruction, "Word is not an instruction"
        return self._flags.value

    @flags.setter
    def flags(self, value: int) -> None:
        assert self.is_instruction, "Word is not an instruction"
        self._flags.value = value

    @property
    def operand(self) -> int:
        assert self.is_instruction, "Word is not an instruction"
        return self._operand.value

    @operand.setter
    def operand(self, value: int) -> None:
        assert self.is_instruction, "Word is not an instruction"
        self._operand.value = value

    @property
    def is_instruction(self) -> bool:
        return self._instruction

    @is_instruction.setter
    def is_instruction(self, switch: bool) -> None:
        if switch:
            # DWord stores value in field `_value`. Here we interpret the value as an instruction after became an IWord.
            if not self._instruction:
                self._instruction = True
                self.value = self._value.value
        else:
            # IWord stores value in a struct. Here we take the interpreted value before became a DWord.
            if self._instruction:
                self._value.value = self.value
                self._instruction = False

    def __eq__(self, o):
        return self.value == o.value

    def __repr__(self):
        if self.is_instruction:
            return f"IWord({self.opcode}, {self.flags}, {self.operand}, lineno={self.lineno})"
        else:
            return f"DWord({self._value.value})"


def IWord(opcode=0, flags=0, operand=0, lineno=0) -> Word:
    """Helper to create an Instruction Word"""
    return Word(opcode, flags, operand, lineno, is_instruction=True)


def DWord(value=0):
    """Helper to create a Data Word"""
    return Word(value=value)
