import unittest

from asm.assembler import assemble
from simulator.cpu import CPU
from simulator.cycle import ExecutionCycle

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

        # Execution cycle receives at start a step function. Here an example:
        messages = []
        def showRegisters(cycle):
            regs = cycle.cpu.registers
            messages.append('AX=%d, BX=%d' % (regs[8].value, regs[9].value))

        # Execution cycle needs a CPU object
        exeCycle = ExecutionCycle(cpu)
        exeCycle.prepare()
        # Test
        self.assertTrue( exeCycle.run(showRegisters) )
