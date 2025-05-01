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


class BaseReg(AbstractData):
    pass


class StructReg(BaseReg, ctypes.Structure):
    pass


class Reg16(StructReg):
    _fields_ = [("value", ctypes.c_uint16)]
    _bits = 16


class Reg8(StructReg):
    _fields_ = [("value", ctypes.c_uint8)]
    _bits = 8


class Reg1(StructReg):
    _fields_ = [("value", ctypes.c_uint8, 1)]
    _bits = 1


class RegX(StructReg):
    _fields_ = [("_h", ctypes.c_uint8),
                ("_l", ctypes.c_uint8)]
    _bits = 16

    def __init__(self, val=0):
        self._h = val >> 8
        self._l = val

    @property
    def h(self):
        return self._h
    @h.setter
    def h(self, val):
        self._h = val

    @property
    def l(self):
        return self._l
    @l.setter
    def l(self, val):
        self._l = val

    @property
    def value(self):
        return self._h << 8 | self._l
    @value.setter
    def value(self, val):
        self._h = val >> 8
        self._l = val


class RegH(BaseReg):
    _bits = 8

    def __init__(self, regx, val=None):
        assert isinstance(regx, RegX)

        self.regx = regx
        if val is not None:
            regx.h = val

    @property
    def value(self):
        return self.regx.h
    @value.setter
    def value(self, val):
        self.regx.h = val


class RegL(BaseReg):
    _bits = 8

    def __init__(self, regx, val=None):
        assert isinstance(regx, RegX)

        self.regx = regx
        if val is not None:
            regx.l = val

    @property
    def value(self):
        return self.regx.l
    @value.setter
    def value(self, val):
        self.regx.l = val
