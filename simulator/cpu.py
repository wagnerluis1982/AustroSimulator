'''Class for CPU simulator functionality

    >>> from asm.assembler import assemble
    >>> asmd = assemble("""
    ...     mov ax, 10
    ...     mov bx, 90
    ...     add ax, bx
    ... """)

    >>> cpu = CPU()
    >>> cpu.set_memory(asmd['words'])
    True
    >>> cpu.set_labels(asmd['labels'])
'''

ADDRESS_SPACE = 256

class CPU(object):
    def __init__(self):
        self._labels = {}
        self._memory = [None]*ADDRESS_SPACE

    def set_labels(self, labels):
        assert isinstance(labels, dict)
        self._labels = labels

        return True

    def set_memory(self, words, start=0):
        assert isinstance(words, list)
        for i in xrange(len(words)):
            self._memory[start] = words[i]
            start += 1

        return True
