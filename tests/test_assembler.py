import pytest
from ply.lex import LexToken

from austro.asm.asm_lexer import LexerException
from austro.asm.assembler import OPCODES, AssembleException, assemble, memory_words
from austro.asm.memword import DWord, IWord


class Test_assemble:
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

    def test_jump_with_register(self):
        """#assemble should be able to jump using a register name"""
        r = assemble("jne ax")

        assert r == {
            "labels": {},
            "words": [
                IWord(4, 0, 128, lineno=1),
            ],
        }

    def test_jump_with_memory_reference(self):
        """#assemble should be able to jump using a memory reference"""
        r = assemble("jne [128]")

        assert r == {
            "labels": {},
            "words": [
                IWord(4, 1, 128, lineno=1),
            ],
        }

    def test_inc_with_memory_reference(self):
        """#assemble should be able to increment using a memory reference"""
        r = assemble("inc [128]")

        assert r == {
            "labels": {},
            "words": [
                IWord(17, 1, 128, lineno=1),
            ],
        }

    def test_shift_with_memory_reference(self):
        """#assemble should be able to shift using a memory reference"""
        r = assemble("shr [128], 1")

        assert r == {
            "labels": {},
            "words": [
                IWord(12, 1, 128, lineno=1),
                DWord(1),
            ],
        }

    def test_error_scanning(self):
        """#assemble should raise error on illegal character"""
        with pytest.raises(LexerException) as e_info:
            assemble("+mov ax, 1")  # symbol '+' is not allowed

        e_info.match(r"Scanning error. Illegal character '\+' at line 1")

    @pytest.mark.parametrize(
        "reg_name, code",
        [
            ("a1", "inc a1"),
            ("a2", "mov ax, a2"),
            ("a3", "mov a3, ax"),
            ("a4", "mov a4, 123"),
            ("a5", "mov a5, [1]"),
            ("a6", "mov [1], a6"),
            ("a7", "shr a7, 1"),
        ],
    )
    def test_error_bad_register(self, reg_name, code):
        """#assemble should raise error on bad register name"""
        with pytest.raises(AssembleException, match=f"bad register name '{reg_name}'"):
            assemble(code)

    def test_error_invalid_opcode(self):
        """#assemble should raise error on invalid opcode"""
        with pytest.raises(AssembleException) as e_info:
            assemble("blah ax, 1")

        e_info.match(r"Invalid token 'blah' at line 1")

    def test_error_missing_comma(self):
        """#assemble should raise error on missing comma"""
        with pytest.raises(AssembleException) as e_info:
            assemble("mov ah 255")

        e_info.match(r"Invalid token '255' at line 1")

    def test_error_invalid_syntax(self):
        """#assemble should raise error on invalid syntax"""
        with pytest.raises(AssembleException) as e_info:
            assemble("mov ax,")

        e_info.match(r"Invalid syntax at line 1")

    def test_error_missing_label(self):
        """#assemble should raise error on jump to undefined label"""
        with pytest.raises(AssembleException) as e_info:
            assemble("jne rambo")

        e_info.match(r"Invalid label 'rambo' at line 1")

    def test_error_duplicated_label(self):
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


class Test_memory_words:
    def test_memory_words(self):
        """#memory_words should return a tuple of Word objects (two at max)"""
        opc = lexToken("OPCODE", "mov", line=1)
        op1 = lexToken("NAME", "ax", line=1)
        op2 = lexToken("NUMBER", 234, line=1)

        assert memory_words(opc, op1, op2), (IWord(2, 2, 8 << 4, lineno=1), DWord(234))

    def test_error_invalid_instruction(self):
        """#memory_words should raise error on invalid opcode"""
        opc = lexToken("OPCODE", "blah", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc)

        e_info.match("Invalid instruction 'BLAH' at line 1")

    def test_error_jump_bad_register(self):
        """#memory_words should raise error on jump to a bad register"""
        opc = lexToken("OPCODE", "jz", line=1)
        op1 = lexToken("NAME", "zz", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1)

        e_info.match("bad register name 'zz'")

    def test_error_jump_invalid_operand(self):
        """#memory_words should raise error on jump with an invalid operand"""
        opc = lexToken("OPCODE", "jz", line=1)
        op1 = lexToken("COMMA", ",", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1)

        e_info.match("Error: invalid operand for 'JZ'")

    def test_error_inc_invalid_operand(self):
        """#memory_words should raise error on increment with an invalid operand"""
        opc = lexToken("OPCODE", "inc", line=1)
        op1 = lexToken("NUMBER", 1, line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1)

        e_info.match("Error: invalid operand for 'INC'")

    def test_error_shift_first_operand_not_reg_or_ref(self):
        """#memory_words should raise error when first operand is neither a register nor a reference"""
        opc = lexToken("OPCODE", "shr", line=1)
        op1 = lexToken("NUMBER", 1, line=1)
        op2 = lexToken("NUMBER", 2, line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1, op2)

        e_info.match("Error: invalid operands for 'SHR'")

    def test_error_shift_second_operand_not_number(self):
        """#memory_words should raise error when second operand is not a number"""
        opc = lexToken("OPCODE", "shr", line=1)
        op1 = lexToken("NAME", "ax", line=1)
        op2 = lexToken("NAME", "bx", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1, op2)

        e_info.match("Error: invalid operands for 'SHR'")

    def test_error_mov_to_number(self):
        """#memory_words should raise error when second operand is not a number"""
        opc = lexToken("OPCODE", "mov", line=1)
        op1 = lexToken("NUMBER", 1, line=1)
        op2 = lexToken("NAME", "ax", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1, op2)

        e_info.match("Error: invalid operands for 'MOV'")

    def test_error_no_arg_with_operand(self):
        """#memory_words should raise error when no-arg opcode has an operand"""
        opc = lexToken("OPCODE", "nop", line=1)
        op1 = lexToken("NAME", "ax", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1)

        e_info.match("Error: operand 'ax' found for no-arg 'NOP'")

    def test_error_1_arg_missing_operand(self):
        """#memory_words should raise error when 1-arg opcode misses the operand"""
        opc = lexToken("OPCODE", "inc", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1=None)

        e_info.match("Error: missing operand for 'INC'")

    def test_error_1_arg_with_second_operand(self):
        """#memory_words should raise error when 1-arg opcode has a second operand"""
        opc = lexToken("OPCODE", "inc", line=1)
        op1 = lexToken("NAME", "ax", line=1)
        op2 = lexToken("NUMBER", 234, line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1, op2)

        e_info.match("Error: second operand '234' found for 1-arg 'INC'")

    def test_error_2_args_missing_operands(self):
        """#memory_words should raise error when 2-args opcode misses operands"""
        opc = lexToken("OPCODE", "mov", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1=None)

        e_info.match("Error: missing operands for 'MOV'")

    def test_error_2_args_missing_first_operand(self):
        """#memory_words should raise error when 2-args opcode misses second operand"""
        opc = lexToken("OPCODE", "mov", line=1)
        op1 = lexToken("NAME", "ax", line=1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc, op1, op2=None)

        e_info.match("Error: missing second operand for 'MOV'")

    def test_error_unknown(self, monkeypatch: pytest.MonkeyPatch):
        """#memory_words should raise error when a misconfigured opcode is introduced"""
        opc = lexToken("OPCODE", "hello", line=1)

        # opcode is in the list of allowed opcodes but it's not implemented
        monkeypatch.setitem(OPCODES, "HELLO", -1)

        with pytest.raises(AssembleException) as e_info:
            memory_words(opc)

        e_info.match("Unknown error while encoding 'HELLO'")


def lexToken(typ, val, line, lexpos=0):
    # Method helper to construct a LexToken
    lt = LexToken()
    lt.type, lt.value, lt.lineno, lt.lexpos = typ, val, line, lexpos
    return lt
