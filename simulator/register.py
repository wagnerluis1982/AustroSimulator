import ctypes


class Reg(ctypes.Structure):
    _fields_ = [("value", ctypes.c_uint16)]


class Reg8(ctypes.Structure):
    _fields_ = [("value", ctypes.c_uint8)]


class Reg1(ctypes.Structure):
    _fields_ = [("value", ctypes.c_uint8, 1)]


class RegX(ctypes.Structure):
    _fields_ = [("_h", ctypes.c_uint8),
                ("_l", ctypes.c_uint8)]

    def __init__(self, val=0):
        self._h = val >> 8
        self._l = val

    @property
    def h(self):
        return self._h
    @h.setter
    def h(self, value):
        self._h = value

    @property
    def l(self):
        return self._l
    @l.setter
    def l(self, value):
        self._l = value

    @property
    def value(self):
        return self._h << 8 | self._l
    @value.setter
    def value(self, val):
        self._h = val >> 8
        self._l = val
