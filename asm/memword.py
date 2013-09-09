import ctypes
from abc import ABCMeta, abstractmethod


class Word(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def set_value(self, value):
        pass

    @property
    def value(self):
        return self.get_value()
    @value.setter
    def value(self, val):
        self.set_value(val)

    def __eq__(self, o):
        return self.value == o.value


class InstructionWord(Word):
    '''Represent the memory instruction word'''

    class Container(ctypes.Structure):
        _fields_ = [('opcode', ctypes.c_ubyte, 5),
                    ('flags', ctypes.c_ubyte, 3),
                    ('operand', ctypes.c_ubyte, 8)]

    def __init__(self, opcode=0, flags=0, operand=0, lineno=0, value=None):
        self._cont = InstructionWord.Container()
        if value is not None:
            self.value = value  # setting whole word
        else:
            self.opcode = opcode
            self.flags = flags
            self.operand = operand
        # Set an associated assembly code line number
        self.lineno = lineno

    def get_value(self):
        return (self.opcode << 3 | self.flags) << 8 | self.operand

    def set_value(self, value):
        self.opcode = value >> 11
        self.flags = value >> 8
        self.operand = value

    @property
    def opcode(self):
        return self._cont.opcode
    @opcode.setter
    def opcode(self, value):
        self._cont.opcode = value

    @property
    def flags(self):
        return self._cont.flags
    @flags.setter
    def flags(self, value):
        self._cont.flags = value

    @property
    def operand(self):
        return self._cont.operand
    @operand.setter
    def operand(self, value):
        self._cont.operand = value

    def __repr__(self):
        return 'InstructionWord(%d, %d, %d, lineno=%d)' % (self.opcode,
                                        self.flags, self.operand, self.lineno)


class DataWord(Word):
    """Represent the memory data word"""

    class Container(ctypes.Structure):
        _fields_ = [('data', ctypes.c_uint16)]


    def __init__(self, value=0):
        self._cont = DataWord.Container()
        self.value = value

    def get_value(self):
        return self._cont.data

    def set_value(self, value):
        self._cont.data = value

    def __repr__(self):
        return 'DataWord(%d)' % (self.value)

