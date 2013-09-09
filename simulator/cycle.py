'''Cycle of execution functionality'''

from abc import ABCMeta, abstractmethod

from simulator.cpu import ADDRESS_SPACE, CPU, Registers


class Stage:
    STOPPED = 0
    FETCH = 1
    DECODE = 2
    EXECUTE = 3
    STORE = 4


class Step(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self._cycle = None

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


class CPUCycle(object):
    def __init__(self, cpu):
        assert isinstance(cpu, CPU)

        self.cpu = cpu
        self.registers = cpu.registers
        self.stage = Stage.STOPPED

    def start(self, step=None):
        step = step if step else DummyStep()
        assert isinstance(step, Step)

        self.registers['PC'] = 0
        while self.registers['PC'] < ADDRESS_SPACE:
            # Fetch stage
            self.stage = Stage.FETCH
            self.cpu.fetch()

            self.registers['PC'] += 1

        return True
