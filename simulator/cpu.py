'''Class for CPU simulator functionality'''

from asm.assembler import REGISTERS
from asm.memword import Word, DataWord
from simulator.register import *


ADDRESS_SPACE = 256

class CPU(object):
    def __init__(self):
        self.memory = Memory(ADDRESS_SPACE)
        self.registers = Registers()

    def set_memory_block(self, words, start=0):
        assert isinstance(words, (list, tuple))
        for i in xrange(len(words)):
            self.memory[start] = words[i]
            start += 1

        return True


class Memory(object):
    def __init__(self, size):
        self._size = size
        self._space = [None]*size

    def __setitem__(self, address, data):
        assert isinstance(address, int)
        assert isinstance(data, (int, Word))

        if address > self._size:
            raise Exception("Address out of memory range")

        if isinstance(data, Word):
            self._space[address] = data
            return
        if not self._space[address]:
            self._space[address] = DataWord()

        self._space[address].value = data

    def __getitem__(self, address):
        assert isinstance(address, int)

        if address > self._size:
            raise Exception("Address out of memory range")
        if not self._space[address]:
            self._space[address] = DataWord()

        return self._space[address].value


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

        # Internal function to set register objects
        def init_register(name, value):
            self._data[Registers.INDEX[name]] = value

        #
        ## Generic registers
        #
        for name in 'AX', 'BX', 'CX', 'DX':
            init_register(name, RegX())
        # 8-bit registers
        for name in 'AH', 'AL', 'BH', 'BL', 'CH', 'CL', 'DH', 'DL':
            reg16 = self[name[0] + 'X']
            init_register(name, reg16)
        # 16-bit only registers
        for name in 'SP', 'BP', 'SI', 'DI':
            init_register(name, Reg())

        #
        ## Specific registers
        #
        for name in 'PC', 'MAR':
            init_register(name, Reg())

        for name in 'RI', 'MBR':
            init_register(name, Reg())

        #
        ## State registers
        #
        for name in 'N', 'Z', 'V', 'T':
            init_register(name, Reg())

    def __setitem__(self, key, value):
        assert isinstance(key, (int, basestring))
        assert isinstance(value, int)

        if isinstance(key, int):
            reg = self._data[key]
        else:
            reg = self._data[Registers.INDEX[key]]

        if key < 8:
            if key & 1:
                reg.h = value
            else:
                reg.l = value
        else:
            reg.value = value

    def __getitem__(self, key):
        assert isinstance(key, (int, basestring))

        if isinstance(key, int):
            reg = self._data[key]
        else:
            reg = self._data[Registers.INDEX[key]]

        if key < 8:
            return reg.h if key & 1 else reg.l
        else:
            return reg.value
