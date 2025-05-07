import unittest

import pytest
from ply.lex import LexToken

from austro.asm.asm_lexer import LexerException
from austro.asm.assembler import AssembleException, assemble, memory_words
from austro.asm.memword import DWord, IWord


class Module_assemble_Test(unittest.TestCase):

    def test_assemble(self):
        """#assemble should work fine with valid code"""
        r = assemble(
            """
            # Load registers
            mov ax, 0xffff
            mov bx, 0

            # Sum with 2 five times
            loop:
            add ax, 2
            inc bx
            cmp bx, 5
            jne loop
            halt
            """
        )

        assert r == {
            "labels": {"loop": 4},
            "words": [
                IWord(2, 2, 128, lineno=3),
                DWord(65535),
                IWord(2, 2, 144, lineno=4),
                DWord(0),
                IWord(16, 2, 128, lineno=8),
                DWord(2),
                IWord(17, 0, 144, lineno=9),
                IWord(27, 2, 144, lineno=10),
                DWord(5),
                IWord(4, 2, 4, lineno=11),
                IWord(1, 0, 0, lineno=12),
            ],
        }

    def test_jump_forward(self):
        """#assemble should be able to jump forward"""
        r = assemble(
            """
            cmp ax, 0
            je quit

            quit:
            halt
            """
        )

        assert r == {
            "labels": {"quit": 3},
            "words": [
                IWord(27, 2, 128, lineno=2),
                DWord(0),
                IWord(3, 2, 3, lineno=3),
                IWord(1, 0, 0, lineno=6),
            ],
        }

    def test_scanning_error(self):
        """#assemble should raise error on illegal character"""
        with pytest.raises(LexerException) as e_info:
            assemble("+mov ax, 1")  # symbol '+' is not allowed

        e_info.match(r"Scanning error. Illegal character '\+' at line 1")

    def test_invalid_opcode(self):
        """#assemble should raise error on invalid opcode"""
        with pytest.raises(AssembleException) as e_info:
            assemble("blah ax, 1")

        e_info.match(r"Invalid token 'blah' at line 1")

    def test_missing_comma(self):
        """#assemble should raise error on missing comma"""
        with pytest.raises(AssembleException) as e_info:
            assemble("mov ah 255")

        e_info.match(r"Invalid token '255' at line 1")

    def test_invalid_syntax(self):
        """#assemble should raise error on invalid syntax"""
        with pytest.raises(AssembleException) as e_info:
            assemble("mov ax,")

        e_info.match(r"Invalid syntax at line 1")

    def test_missing_label(self):
        """#assemble should raise error on jump to undefined label"""
        with pytest.raises(AssembleException) as e_info:
            assemble("jne rambo")

        e_info.match(r"Invalid label 'rambo' at line 1")

    def test_duplicated_label(self):
        """#assemble should raise error on label double defined"""
        with pytest.raises(AssembleException) as e_info:
            assemble(
                """
                rambo:
                mov ax, 1
                rambo:
                mov bx, 1
                """
            )

        e_info.match(r"Error: symbol 'rambo' is already defined at line 4")


class Module_memory_words_Test(unittest.TestCase):

    def test_memory_words(self):
        """#memory_words should return a tuple of Word objects (two at max)"""
        opc = lexToken("OPCODE", "mov", line=1)
        op1 = lexToken("NAME", "ax", line=1)
        op2 = lexToken("NUMBER", 234, line=1)

        self.assertEqual(
            memory_words(opc, op1, op2), (IWord(2, 2, 8 << 4, lineno=1), DWord(234))
        )


def lexToken(typ, val, line, lexpos=0):
    # Method helper to construct a LexToken
    lt = LexToken()
    lt.type, lt.value, lt.lineno, lt.lexpos = typ, val, line, lexpos
    return lt
