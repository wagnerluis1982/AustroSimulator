import unittest

from asm.assembler import assemble, REGISTERS
from simulator import CPU, MachineCycle, Step
from simulator.cpu import Registers


# The cycle receives at start a Step class instance. Here a simple example:
class ShowRegisters(Step):
    def __init__(self, *names):
        self.messages = []
        self.fmt = ','.join(['%s=%%d' % nm for nm in names])

        indexes = []
        for nm in names:
            try:
                indexes.append(REGISTERS[nm])
            except KeyError:
                indexes.append(getattr(Registers, nm))
        self.indexes = indexes

    def do(self):
        args = [self.cycle.cpu.registers[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


class ShowMemories(Step):
    def __init__(self, *numbers):
        self.messages = []
        self.fmt = ','.join(['[%d]=%%d' % n for n in numbers])
        self.indexes = numbers

    def do(self):
        args = [self.cycle.cpu.memory[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


class TestMachineCycle(unittest.TestCase):
    '''MachineCycle'''

    def test_mov__reg_reg(self):
        '''mov should load a register from another register'''

        # mov instructions
        assembly = ("mov ax, 3\n"
                    "mov bx, ax\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',  # start
                    'AX=3,BX=0',  # after "mov ax, 3"
                    'AX=3,BX=3',  # after "mov bx, ax"
                    'AX=3,BX=3']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__reg_const(self):
        '''mov should load a register from a constant'''

        # mov instructions
        assembly = ("mov ax, 9\n"
                    "mov bx, 4\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',  # start
                    'AX=9,BX=0',  # after "mov ax, 9"
                    'AX=9,BX=4',  # after "mov bx, 4"
                    'AX=9,BX=4']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__reg_mem(self):
        '''mov should load a register from a memory position'''

        # mov instructions
        assembly = ("mov ax, 7\n"
                    "mov [128], ax\n"
                    "mov bx, [128]\n"
                    "halt\n")
        # registers
        registers = ('BX',)
        # expected messages
        messages = ['BX=0',  # start
                    'BX=0',  # after "mov ax, 7"
                    'BX=0',  # after "mov [128], ax"
                    'BX=7',  # after "mov bx, [128]"
                    'BX=7']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__mem_reg(self):
        '''mov should load a memory position from a register'''

        # mov instructions
        assembly = ("mov ax, 5\n"
                    "mov [128], ax\n"
                    "halt\n")
        # memory addresses
        memories = (128,)
        # expected messages
        messages = ['[128]=0',  # start
                    '[128]=0',  # after "mov ax, 5"
                    '[128]=5',  # after "mov [128], ax"
                    '[128]=5']  # after "halt"

        self.memory_asserts(assembly, memories, messages)

    def register_asserts(self, assembly, registers, messages):
        # mov instructions
        asmd = assemble(assembly)

        cpu = CPU()
        cpu.set_memory_block(asmd['words'])

        # Cycle needs a CPU object
        mach_cycle = MachineCycle(cpu)
        # Test run
        show = ShowRegisters(*registers)
        self.assertTrue( mach_cycle.start(show) )

        # Test step
        self.assertEqual( show.messages, messages )

    def memory_asserts(self, assembly, addresses, messages):
        # mov instructions
        asmd = assemble(assembly)

        cpu = CPU()
        cpu.set_memory_block(asmd['words'])

        # Cycle needs a CPU object
        mach_cycle = MachineCycle(cpu)
        # Test run
        show = ShowMemories(*addresses)
        self.assertTrue( mach_cycle.start(show) )

        # Test step
        self.assertEqual( show.messages, messages )
