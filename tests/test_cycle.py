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


class TestMachineCycle(unittest.TestCase):
    '''MachineCycle'''

    def test_mov__reg_const(self):
        '''mov should load registers with a constant'''

        # mov instructions
        asmd = assemble("""
            mov ax, 9
            mov bx, 4
            mov cx, ax
            halt
        """)

        cpu = CPU()
        cpu.set_memory_block(asmd['words'])

        # Cycle needs a CPU object
        mach_cycle = MachineCycle(cpu)
        # Test run
        show = ShowRegisters('AX', 'BX', 'CX')
        self.assertTrue( mach_cycle.start(show) )

        # Test step
        self.assertEqual( show.messages,
                    ['AX=0,BX=0,CX=0',   # start
                     'AX=9,BX=0,CX=0',   # after "mov ax, 9"
                     'AX=9,BX=4,CX=0',   # after "mov bx, 4"
                     'AX=9,BX=4,CX=9',   # after "mov cx, ax"
                     'AX=9,BX=4,CX=9']   # after "halt"
                )
