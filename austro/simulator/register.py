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

from typing import Protocol

from austro.shared import AbstractData


class c_number_type(Protocol):
    @property
    def value(self): ...

    @value.setter
    def value(self, val): ...


class BaseReg(AbstractData):
    def __init__(self, value: c_number_type):
        self._value = value

    @property
    def value(self) -> int:
        return self._value.value

    @value.setter
    def value(self, val: int) -> None:
        self._value.value = val


class StructReg(BaseReg, ctypes.Structure):
    pass


class Reg16(BaseReg):
    bits = 16

    def __init__(self):
        super().__init__(ctypes.c_uint16())


class RegX(StructReg):
    bits = 16

    _fields_ = (
        ("_h", ctypes.c_uint8),
        ("_l", ctypes.c_uint8),
    )

    def __init__(self, val=0):
        self._h = val >> 8
        self._l = val

    @property
    def high(self):
        return self._h

    @high.setter
    def high(self, val):
        self._h = val

    @property
    def low(self):
        return self._l

    @low.setter
    def low(self, val):
        self._l = val

    @property
    def value(self):
        return self._h << 8 | self._l

    @value.setter
    def value(self, val):
        self._h = val >> 8
        self._l = val


class RegH(BaseReg):
    bits = 8

    def __init__(self, regx: RegX):
        assert isinstance(regx, RegX)
        self.regx = regx

    @property
    def value(self):
        return self.regx.high

    @value.setter
    def value(self, val):
        self.regx.high = val


class RegL(BaseReg):
    bits = 8

    def __init__(self, regx: RegX):
        assert isinstance(regx, RegX)
        self.regx = regx

    @property
    def value(self):
        return self.regx.low

    @value.setter
    def value(self, val):
        self.regx.low = val
