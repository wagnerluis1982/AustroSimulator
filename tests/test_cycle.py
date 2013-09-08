import unittest

from asm.assembler import assemble
from simulator import CPU, ExecutionCycle, Step

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

        # The cycle receives at start a Step class instance. A simple example:
        class ShowRegisters(Step):
            messages = []

            def do(self):
                regs = self.cycle.cpu.registers
                self.messages.append('AX=%d, BX=%d' % (regs[8].value,
                                                       regs[9].value))

        # Execution cycle needs a CPU object
        exec_cycle = ExecutionCycle(cpu)
        exec_cycle.prepare()
        # Test
        show_regs = ShowRegisters()
        self.assertTrue( exec_cycle.run(show_regs) )
