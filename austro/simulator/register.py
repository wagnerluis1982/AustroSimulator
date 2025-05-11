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


class BaseReg(BaseData):
    pass


class Reg16(BaseReg):
    bits = 16

    def __init__(self):
        super().__init__(ctypes.c_uint16())


class RegX(Reg16):
    @property
    def high(self) -> int:
        return self.value >> 8

    @high.setter
    def high(self, val: int) -> None:
        self.value = self.low | (val << 8)

    @property
    def low(self) -> int:
        return self.value & 0x00FF

    @low.setter
    def low(self, val: int) -> None:
        self.value = self.high | (val & 0x00FF)


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
