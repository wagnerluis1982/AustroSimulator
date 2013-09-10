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
            self.memory.set_word(start, words[i])
            start += 1

        return True


class Memory(object):
    def __init__(self, size):
        self._size = size
        self._space = [None]*size

    def set_word(self, address, word):
        assert isinstance(address, int)
        assert isinstance(word, Word)

        if not (0 <= address < self._size):
            raise Exception("Address out of memory range")

        self._space[address] = word

    def get_word(self, address):
        assert isinstance(address, int)

        if not (0 <= address < self._size):
            raise Exception("Address out of memory range")
        if not self._space[address]:
            self._space[address] = DataWord()

        return self._space[address]

    def __setitem__(self, address, data):
        assert isinstance(address, int)
        assert isinstance(data, int)

        if not (0 <= address < self._size):
            raise Exception("Address out of memory range")
        if not self._space[address]:
            self._space[address] = DataWord()

        self._space[address].value = data

    def __getitem__(self, address):
        assert isinstance(address, int)

        if not (0 <= address < self._size):
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
        self._regs = {}
        self._words = {}

        # Internal function to set register objects
        def init_register(name, value):
            self._regs[Registers.INDEX[name]] = value

        #
        ## Generic registers
        #
        for name in 'AX', 'BX', 'CX', 'DX':
            init_register(name, RegX())
        # 8-bit most significant registers
        for name in 'AH', 'BH', 'CH', 'DH':
            regx = self._regs[Registers.INDEX[name[0] + 'X']]
            init_register(name, RegH(regx))
        # 8-bit less significant registers
        for name in 'AL', 'BL', 'CL', 'DL':
            regx = self._regs[Registers.INDEX[name[0] + 'X']]
            init_register(name, RegL(regx))
        # 16-bit only registers
        for name in 'SP', 'BP', 'SI', 'DI':
            init_register(name, Reg16())

        #
        ## Specific registers
        #
        for name in 'PC', 'MAR':
            init_register(name, Reg16())

        for name in 'RI', 'MBR':
            init_register(name, Reg16())

        #
        ## State registers
        #
        for name in 'N', 'Z', 'V', 'T':
            init_register(name, Reg16())

    def set_word(self, key, word):
        assert isinstance(key, (int, basestring))
        assert isinstance(word, Word)

        if isinstance(key, basestring):
            key = Registers.INDEX[key]

        self._words[key] = word
        self[key] = word.value
        if self[key] != word.value:
            raise Exception("Word data too large for the register")

    def get_word(self, key):
        assert isinstance(key, (int, basestring))

        if isinstance(key, basestring):
            key = Registers.INDEX[key]

        return self._words[key]

    def __setitem__(self, key, value):
        assert isinstance(key, (int, basestring))
        assert isinstance(value, int)

        if isinstance(key, int):
            reg = self._regs[key]
        else:
            reg = self._regs[Registers.INDEX[key]]

        reg.value = value

    def __getitem__(self, key):
        assert isinstance(key, (int, basestring))

        if isinstance(key, int):
            reg = self._regs[key]
        else:
            reg = self._regs[Registers.INDEX[key]]

        return reg.value
