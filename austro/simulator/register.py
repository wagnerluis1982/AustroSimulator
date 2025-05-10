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

from typing import override

from austro.shared import AbstractData


class BaseReg[T](AbstractData):
    _value: T

    @property
    @override
    def value(self) -> int:
        return self._value.value  # type:ignore

    @value.setter
    @override
    def value(self, val: int):
        self._value.value = val  # type:ignore


class StructReg(BaseReg, ctypes.Structure):
    pass


class Reg16(StructReg):
    bits = 16
    _fields_ = (("value", ctypes.c_uint16),)


class Reg8(StructReg):
    bits = 8
    _fields_ = (("value", ctypes.c_uint8),)


class Reg1(StructReg):
    bits = 1
    _fields_ = (("value", ctypes.c_uint8, 1),)


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
    regx: RegX

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
    regx: RegX

    def __init__(self, regx: RegX):
        assert isinstance(regx, RegX)
        self.regx = regx

    @property
    def value(self):
        return self.regx.low

    @value.setter
    def value(self, val):
        self.regx.low = val
