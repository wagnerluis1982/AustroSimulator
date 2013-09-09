import unittest

from asm.assembler import assemble, REGISTERS
from simulator import CPU, CPUCycle, Step
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
        args = [self.cycle.cpu.registers[i].value for i in self.indexes]
        self.messages.append(self.fmt % args)


class TestCPUCycle(unittest.TestCase):
    '''CPUCycle'''

    def test_mov__reg_const(self):
        '''mov should load registers with a constant'''

        # mov instructions
        asmd = assemble("""
            mov ax, 9
            mov bx, 4
            halt
        """)

        cpu = CPU()
        cpu.set_memory(asmd['words'])

        # Cycle needs a CPU object
        cpu_cycle = CPUCycle(cpu)
        cpu_cycle.prepare()
        # Test run
        show = ShowRegisters('AX', 'BX')
        self.assertTrue( cpu_cycle.run(show) )
