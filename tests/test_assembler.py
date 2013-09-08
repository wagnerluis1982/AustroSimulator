import unittest

from ply.lex import LexToken
from asm.assembler import InstructionWord, DataWord, memory_words

class InstructionWordTest(unittest.TestCase):
    """InstructionWord"""

    def test_constructor_3_args(self):
        """constructor(opcode, flags, operand) should set value"""
        iw = InstructionWord(0b00001, 0b010, 0b00000011)
        self.assertEqual( iw.value, 0b101000000011 )

    def test_constructor_1_arg(self):
        """constructor(value=arg) should set opcode, flags, operand"""
        iw = InstructionWord(value=0b101000000011)
        self.assertEqual( (iw.opcode, iw.flags, iw.operand),
                          (0b00001, 0b010, 0b00000011) )

    def test_set_value(self):
        """setting value should set opcode, flags, operand"""
        iw = InstructionWord()
        iw.value = 0b101000000011
        self.assertEqual( (iw.opcode, iw.flags, iw.operand),
                          (0b00001, 0b010, 0b00000011) )


class ModuleTest(unittest.TestCase):
    def test_memory_words(self):
        """#memory_words should return a tuple of Word objects (two in max)"""
        opc = self.lexToken('OPCODE', 'mov', line=1)
        op1 = self.lexToken('NAME', 'ax', line=1)
        op2 = self.lexToken('NUMBER', 234, line=1)

        self.assertEqual( memory_words(opc, op1, op2),
                (InstructionWord(2, 2, 8, lineno=1), DataWord(234)) )

    def lexToken(self, typ, val, line, lexpos=0):
        # Method helper to construct a LexToken
        lt = LexToken()
        lt.type, lt.value, lt.lineno, lt.lexpos = typ, val, line, lexpos
        return lt
