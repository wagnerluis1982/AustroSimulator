import unittest

from ply.lex import LexToken
from austro.asm.assembler import Word, memory_words


class ModuleTest(unittest.TestCase):
    """asm.assembler"""

    def test_memory_words(self):
        """#memory_words should return a tuple of Word objects (two at max)"""
        opc = self.lexToken('OPCODE', 'mov', line=1)
        op1 = self.lexToken('NAME', 'ax', line=1)
        op2 = self.lexToken('NUMBER', 234, line=1)

        self.assertEqual( memory_words(opc, op1, op2),
                (Word(2, 2, 8 << 4, lineno=1, is_instruction=True), Word(234)) )

    def lexToken(self, typ, val, line, lexpos=0):
        # Method helper to construct a LexToken
        lt = LexToken()
        lt.type, lt.value, lt.lineno, lt.lexpos = typ, val, line, lexpos
        return lt
