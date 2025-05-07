import unittest

from austro.asm.memword import DWord, IWord, Word


class WordTest(unittest.TestCase):
    def test_flag_is_instruction(self):
        w = Word(value=0)
        assert not w.is_instruction

        w.is_instruction = True
        assert w.is_instruction

        # set value when is_instruction == True
        w.value = 0xffff
        assert w._opcode == 31
        assert w._flags == 7
        assert w._operand == 255

        # convert IWord to DWord
        w.is_instruction = False
        assert w._value == 0xffff

    def test_instruction_word_repr(self):
        assert repr(IWord(1, 2, 3, 4)) == "IWord(1, 2, 3, lineno=4)"

    def test_data_word_repr(self):
        assert repr(DWord(123)) == "DWord(123)"
