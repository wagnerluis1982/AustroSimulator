'''Class for CPU simulator functionality'''

from asm.assembler import REGISTERS
from simulator.register import *


ADDRESS_SPACE = 256

class CPU(object):
    def __init__(self):
        self._labels = {}
        self._memory = [None]*ADDRESS_SPACE
        self._registers = Registers()

    def fetch(self):
        pass

    def set_memory(self, words, start=0):
        assert isinstance(words, list)
        for i in xrange(len(words)):
            self._memory[start] = words[i]
            start += 1

        return True

    @property
    def registers(self):
        return dict(self._registers)


class Registers(dict):
    '''Container to store the CPU registers'''

    # Specific registers
    PC = 16
    RI = 17
    MAR = 18
    MBR = 19

    # State registers
    N = 20
    Z = 21
    V = 22
    T = 23

    def __init__(self):
        # AX, BX, CX, DX
        for i in xrange(8, 12):
            dict.__setitem__(self, i, RegX())
        # AH, AL, BH, BL, CH, CL, DH. DL
        for i in xrange(8):
            xkey = i+7 if i & 1 else i+8  # get AX, BX, CX, DX keys
            dict.__setitem__(self, xkey, RegX())
        # SP, BP, SI, DI
        for i in xrange(12, 16):
            dict.__setitem__(self, i, Reg())
        #
        # Specific registers
        #
        for i in 'PC', 'MAR':
            dict.__setitem__(self, getattr(self, i), Reg8())

        for i in 'RI', 'MBR':
            dict.__setitem__(self, getattr(self, i), Reg())

        # State registers
        for i in 'N', 'Z', 'V', 'T':
            dict.__setitem__(self, getattr(self, i), Reg1())

    def __setitem__(self, key, value):
        assert isinstance(key, int)
        assert isinstance(value, int)

        reg = self[key]
        if key < 8:
            if key & 1:
                reg.h = value
            else:
                reg.l = value
        else:
            reg.value = value

    def __getitem__(self, key):
        assert isinstance(key, int)

        reg = dict.__getitem__(self, key)
        if key < 8:
            return reg.h if key & 1 else reg.l
        else:
            return reg.value
