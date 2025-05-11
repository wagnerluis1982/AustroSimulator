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

from abc import ABCMeta, abstractmethod
from typing import ClassVar


class AbstractData(metaclass=ABCMeta):
    bits: ClassVar[int]

    @property
    @abstractmethod
    def value(self) -> int: ...

    @value.setter
    @abstractmethod
    def value(self, value: int): ...


class AustroException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
