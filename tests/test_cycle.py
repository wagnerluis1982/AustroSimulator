import unittest

from asm.assembler import assemble, REGISTERS
from simulator import CPU, ExecutionCycle, Step
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


class TestExecutionCycle(unittest.TestCase):
    '''ExecutionCycle'''

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

        # Execution cycle needs a CPU object
        exec_cycle = ExecutionCycle(cpu)
        exec_cycle.prepare()
        # Test run
        show = ShowRegisters('AX', 'BX')
        self.assertTrue( exec_cycle.run(show) )
