from __future__ import annotations

from austro.asm.memword import DWord, IWord, Word


class TestWord:
    def test_flag_is_instruction(self):
        w = Word(value=0)
        assert not w.is_instruction

        w.is_instruction = True
        assert w.is_instruction

        # set value when is_instruction == True
        w.value = 0xffff  # fmt: skip
        assert w.opcode == 31
        assert w.flags == 7
        assert w.operand == 255

        # convert IWord to DWord
        w.is_instruction = False
        assert w.value == 0xffff  # fmt: skip

    def test_is_instance_Word(self):
        w = Word(value=0)

        assert isinstance(w, Word)

    def test_is_instance_IWord(self):
        w = Word(is_instruction=True)

        assert isinstance(w, IWord)

    def test_is_instance_DWord(self):
        w = Word(value=0, is_instruction=False)

        assert isinstance(w, DWord)

    def test_is_not_instance_str(self):
        assert not isinstance("str", Word)

    def test_instruction_word_repr(self):
        assert repr(IWord(1, 2, 3, 4)) == "IWord(1, 2, 3, lineno=4)"

    def test_data_word_repr(self):
        assert repr(DWord(123)) == "DWord(123)"
