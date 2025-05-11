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

from typing import ClassVar, Protocol


class c_number_type(Protocol):
    @property
    def value(self): ...

    @value.setter
    def value(self, val): ...


class BaseData:
    bits: ClassVar[int]

    def __init__(self, value: c_number_type):
        self._value = value

    @property
    def value(self) -> int:
        return self._value.value

    @value.setter
    def value(self, val: int) -> None:
        self._value.value = val


class AustroException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
