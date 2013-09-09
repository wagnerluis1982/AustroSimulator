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
        return dict(self._registers._data)  # private violation


class Registers(object):
    '''Container to store the CPU registers'''

    # Map of register names as keys and it number identifiers as values
    INDEX = dict(REGISTERS.items() + [
            # Specific registers
            ('PC', 16),
            ('RI', 17),
            ('MAR', 18),
            ('MBR', 19),
            # State registers
            ('N', 20),
            ('Z', 21),
            ('V', 22),
            ('T', 23),
        ])

    def __init__(self):
        self._data = {}
        #
        ## Generic registers
        #
        for name in 'AX', 'BX', 'CX', 'DX':
            self._data[Registers.INDEX[name]] = RegX()
        # 8-bit registers
        for name in 'AH', 'AL', 'BH', 'BL', 'CH', 'CL', 'DH', 'DL':
            reg16 = self._data[Registers.INDEX[name[0] + 'X']]
            self._data[Registers.INDEX[name]] = reg16
        # 16-bit only registers
        for name in 'SP', 'BP', 'SI', 'DI':
            self._data[Registers.INDEX[name]] = Reg()

        #
        ## Specific registers
        #
        for name in 'PC', 'MAR':
            self._data[Registers.INDEX[name]] = Reg()

        for name in 'RI', 'MBR':
            self._data[Registers.INDEX[name]] = Reg()

        #
        ## State registers
        #
        for name in 'N', 'Z', 'V', 'T':
            self._data[Registers.INDEX[name]] = Reg()

    def __setitem__(self, key, value):
        assert isinstance(key, int)
        assert isinstance(value, int)

        reg = self._data[key]
        if key < 8:
            if key & 1:
                reg.h = value
            else:
                reg.l = value
        else:
            reg.value = value

    def __getitem__(self, key):
        assert isinstance(key, int)

        reg = self._data[key]
        if key < 8:
            return reg.h if key & 1 else reg.l
        else:
            return reg.value
