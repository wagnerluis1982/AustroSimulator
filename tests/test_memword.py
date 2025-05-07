import unittest

from austro.asm.memword import DWord, IWord


class IWordTest(unittest.TestCase):
    def test_repr(self):
        assert repr(IWord(1, 2, 3, 4)) == "IWord(1, 2, 3, lineno=4)"


class DWordTest(unittest.TestCase):
    def test_repr(self):
        assert repr(DWord(123)) == "DWord(123)"
