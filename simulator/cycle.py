'''Cycle of execution functionality

    >>> from asm.assembler import assemble
    >>> asmd = assemble("""
    ...     mov ax, 10
    ...     mov bx, 90
    ...     add ax, bx
    ... """)

    >>> from simulator.cpu import CPU
    >>> cpu = CPU()
    >>> cpu.set_memory(asmd['words'])
    True
    >>> cpu.set_labels(asmd['labels'])

    The execution execution cycle receive at start a step function. Here an
    example.

    >>> def showRegisters(cycle):
    ...     import sys
    ...     regs = cycle.cpu.registers
    ...     sys.stderr.write('AX=%d, BX=%d\\n' % (regs[8].value,
    ...                                           regs[9].value))

    >>> exeCycle = ExecutionCycle(cpu)
    >>> exeCycle.prepare()
    >>> exeCycle.run(showRegisters)
    True
'''

from simulator.cpu import CPU, Registers


class MicroStep(object):
    STOPPED = 0
    FETCH = 1
    DECODE = 2
    EXECUTE = 3
    STORE = 4


class ExecutionCycle(object):
    def __init__(self, cpu):
        assert isinstance(cpu, CPU)
        self.cpu = cpu
        self.stage = 0

    def prepare(self):
        self.PC = 0

    def run(self, fnStep=lambda:None):
        return True

    @property
    def PC(self):
        return self.cpu.registers[Registers.PC]

    @PC.setter
    def PC(self, value):
        self.cpu.registers[Registers.PC] = value
