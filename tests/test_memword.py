import unittest

from asm.memword import InstructionWord, DataWord


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
