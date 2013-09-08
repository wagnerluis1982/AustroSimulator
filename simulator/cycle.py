'''Cycle of execution functionality'''

from simulator.cpu import ADDRESS_SPACE, CPU, Registers


class Stage:
    STOPPED = 0
    FETCH = 1
    DECODE = 2
    EXECUTE = 3
    STORE = 4


class Step(object):
    pass


class ExecutionCycle(object):
    def __init__(self, cpu):
        assert isinstance(cpu, CPU)
        self.cpu = cpu
        self.stage = Stage.STOPPED

    def prepare(self):
        self.PC = 0

    def run(self, step=DummyStep()):
        while self.PC < ADDRESS_SPACE:
            # Fetch stage
            self.stage = Stage.FETCH
            self.cpu.fetch()

        return True

    @property
    def PC(self):
        return self.cpu.registers[Registers.PC]

    @PC.setter
    def PC(self, value):
        self.cpu.registers[Registers.PC] = value


class DummyStep(Step):
    pass
