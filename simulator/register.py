import ctypes


class BaseReg(object):
    pass


class StructReg(BaseReg, ctypes.Structure):
    pass


class Reg16(StructReg):
    _fields_ = [("value", ctypes.c_uint16)]


class Reg8(StructReg):
    _fields_ = [("value", ctypes.c_uint8)]


class Reg1(StructReg):
    _fields_ = [("value", ctypes.c_uint8, 1)]


class RegX(StructReg):
    _fields_ = [("_h", ctypes.c_uint8),
                ("_l", ctypes.c_uint8)]

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
