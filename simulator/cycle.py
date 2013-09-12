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
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

'''Machine cycle functionality'''

from abc import ABCMeta, abstractmethod

from asm.assembler import OPCODES
from simulator.cpu import ADDRESS_SPACE, CPU, Registers


class Stage:
    STOPPED = 0
    FETCH = 1
    DECODE = 2
    EXECUTE = 3
    STORE = 4
    HALTED = 5


class Step(object):
    __metaclass__ = ABCMeta
    _cycle = None

    @abstractmethod
    def do(self):
        pass

    @property
    def cycle(self):
        return self._cycle
    @cycle.setter
    def cycle(self, value):
        self._cycle = value


class DummyStep(Step):
    def do(self):
        pass


class Decode(object):
    opcode = None
    op1 = None
    op2 = None
    store = None


class MachineCycle(object):
    def __init__(self, cpu):
        assert isinstance(cpu, CPU)

        self.cpu = cpu
        self.stage = Stage.STOPPED

    def start(self, step=None):
        step = step if step else DummyStep()
        assert isinstance(step, Step)
        step.cycle = self

        registers = self.cpu.registers
        memory = self.cpu.memory
        _ = self._opcodes  # alias to improve code visual

        registers['PC'] = 0
        self.stage = Stage.FETCH
        while True:
            if registers['PC'] >= ADDRESS_SPACE:
                raise Exception("PC register greater than address space")

            # Fetch stage
            if self.stage == Stage.FETCH:
                step.do()  # step action
                registers['MAR'] = registers['PC']
                registers.set_word('MBR', memory.get_word(registers['MAR']))
                registers.set_word('RI', registers.get_word('MBR'))
                self.stage = Stage.DECODE
            # Decode stage
            elif self.stage == Stage.DECODE:
                decode = self.decode(registers.get_word('RI'))
                registers['PC'] += 1
                self.stage = Stage.EXECUTE
            # Execute stage
            elif self.stage == Stage.EXECUTE:
                opcode = decode.opcode
                if opcode in _('MOV'):
                    registers[decode.op1] = registers[decode.op2]
                elif opcode in _('NOP'):
                    self.stage = Stage.FETCH
                    continue
                elif opcode in _('HALT'):
                    break

                # Next stage: store or fetch
                if decode.store is not None:
                    self.stage = Stage.STORE
                else:
                    self.stage = Stage.FETCH
            # Store stage
            elif self.stage == Stage.STORE:
                memory[decode.store] = registers[decode.op1]
                self.stage = Stage.FETCH

        self.stage = Stage.HALTED
        step.do()  # last step action

        return True

    def _opcodes(self, *opnames):
        for name in opnames:
            yield OPCODES[name]

    def _arg_type(self, opcode):
        DST_ORI = (0b00010, 0b10000, 0b10011, 0b10100, 0b10101, 0b10110,
                   0b11000, 0b11001, 0b11010,)
        if opcode in DST_ORI:
            return 'DST_ORI'

        OP1_OP2 = (11011,)
        if opcode in OP1_OP2:
            return 'OP1_OP2'

        OP_QNT = (0b01101, 0b01110,)
        if opcode in OP_QNT:
            return 'OP_QNT'

        JUMP = range(0b00011, 0b01100+1)
        if opcode in JUMP:
            return 'JUMP'

        OP = (0b10001, 0b10010, 0b10111,)
        if opcode in OP:
            return 'OP'

        return 'NOARG'

    def decode(self, instr_word):
        dcd = Decode()
        dcd.opcode = instr_word.opcode

        registers = self.cpu.registers
        memory = self.cpu.memory

        argtype = self._arg_type(instr_word.opcode)

        if argtype == 'NOARG':
            return dcd

        flags = instr_word.flags
        operand = instr_word.operand
        if argtype in ('DST_ORI', 'OP1_OP2'):
            order = flags & 0b011
            # Reg, Reg
            if order == 0:
                dcd.op1 = operand >> 4
                dcd.op2 = operand & 0b1111
            # Situations that need next word
            else:
                registers['PC'] += 1  # increment PC
                registers['MAR'] = registers['PC']
                registers['MBR'] = memory[registers['MAR']]
                # Reg, Mem
                if order == 1:
                    dcd.op1 = operand
                    # Getting memory reference
                    registers['PC'] = registers['MBR']
                    registers['TMP'] = memory[registers['PC']]
                    dcd.op2 = Registers.INDEX['TMP']
                    registers['PC'] = registers['MAR']
                # Reg, Const
                elif order == 2:
                    dcd.op1 = operand
                    dcd.op2 = Registers.INDEX['MBR']
                # Mem, Reg
                else:
                    dcd.op2 = operand
                    # Getting memory reference
                    registers['PC'] = registers['MBR']
                    registers['TMP'] = memory[registers['PC']]
                    dcd.op1 = Registers.INDEX['TMP']
                    registers['PC'] = registers['MAR']
                    # Setting for store stage
                    dcd.store = registers['MBR']

            # Signed operation flag
            dcd.signed = bool(flags & 0b100)

            return dcd
