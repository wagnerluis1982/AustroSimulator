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
        super().__init__(ctypes.c_uint16())

        # Flag to know if this word should act as an instruction
        self._instruction = is_instruction
        # Set an associated assembly code line number (for instructions)
        self.lineno = lineno

        # In an instruction word, the 16 bits = 5 (opcode) + 3 (flags) + 8 (operand)
        if is_instruction:
            _opcode = (opcode & 0x1F) << 11
            _flags = (flags & 0x07) << 8
            _operand = operand & 0xFF
            self.value = _opcode | _flags | _operand
        # In a data word the 'value' must be set
        else:
            assert value is not None, "DWord requires 'value' but was not set"
            self.value = value

    @property
    def opcode(self) -> int:
        assert self.is_instruction, "Word is not an instruction"
        return self.value >> 11

    @opcode.setter
    def opcode(self, val: int) -> None:
        assert self.is_instruction, "Word is not an instruction"
        self.value = (self.value & 0x07FF) | ((val & 0x001F) << 11)

    @property
    def flags(self) -> int:
        assert self.is_instruction, "Word is not an instruction"
        return (self.value >> 8) & 0x0007

    @flags.setter
    def flags(self, val: int) -> None:
        assert self.is_instruction, "Word is not an instruction"
        self.value = (self.value & 0xF8FF) | ((val & 0x0007) << 8)

    @property
    def operand(self) -> int:
        assert self.is_instruction, "Word is not an instruction"
        return self.value & 0x00FF

    @operand.setter
    def operand(self, val: int) -> None:
        assert self.is_instruction, "Word is not an instruction"
        self.value = (self.value & 0xFF00) | (val & 0x00FF)

    @property
    def is_instruction(self) -> bool:
        return self._instruction

    @is_instruction.setter
    def is_instruction(self, switch: bool) -> None:
        self._instruction = switch

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Word) and self.value == o.value

    def __repr__(self) -> str:
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
