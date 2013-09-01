# Austro Simulator Assembler

# NOTE: This was intended to be a parser, but it isn't due to lack of knowledge.

import ctypes

from asm_lexer import lexer

class InstructionWord(ctypes.Structure):
    """Represent the memory instruction word

        >>> print bin(InstructionWord(0b00001, 0b010, 0b00000011).value)
        0b101000000011
    """
    _fields_ = [('opcode', ctypes.c_ubyte, 5),
                ('flags', ctypes.c_ubyte, 3),
                ('operand', ctypes.c_ubyte, 8)]

    @property
    def value(self):
        return (self.opcode << 3 | self.flags) << 8 | self.operand

    def __repr__(self):
        return 'InstructionWord(%d, %d, %d)' % (self.opcode, self.flags,
                                                self.operand)

class DataWord(ctypes.Structure):
    """Represent the memory data word"""
    _fields_ = [('value', ctypes.c_uint16)]

    def __repr__(self):
        return 'DataWord(%d)' % (self.value)

OPCODES = {
        'NOP': 0b00000, 'HALT': 0b00001, 'MOV': 0b00010, 'JZ':   0b00011,
        'JE':  0b00101, 'JNZ':  0b00110, 'JNE': 0b00110, 'JN':   0b00111,
        'JLT': 0b00111, 'JP':   0b01000, 'JGT': 0b01000, 'JGE':  0b01001,
        'JLE': 0b01001, 'JV':   0b01010, 'JT':  0b01011, 'JMP':  0b01100,
        'SHR': 0b01101, 'SHL':  0b01110, 'ADD': 0b10000, 'IADD': 0b10000,
        'INC': 0b10001, 'DEC':  0b10010, 'SUB': 0b10011, 'ISUB': 0b10011,
        'MUL': 0b10100, 'IMUL': 0b10100, 'OR':  0b10101, 'AND':  0b10110,
        'NOT': 0b10111, 'XOR':  0b11000, 'DIV': 0b11001, 'IDIV': 0b11001,
        'MOD': 0b11010, 'IMOD': 0b11010, 'CMP': 0b11011, 'ICMP': 0b11011,
    }

REGISTERS = {
        'AL': 0b0000, 'AH': 0b0001, 'BL': 0b0010, 'BH': 0b0011,
        'CL': 0b0100, 'CH': 0b0101, 'DL': 0b0110, 'DH': 0b0111,
        'AX': 0b1000, 'BX': 0b1001, 'CX': 0b1010, 'DX': 0b1011,
        'SP': 0b1100, 'BP': 0b1101, 'SI': 0b1110, 'DI': 0b1111,
    }

def instruction_words(opcode, op1=None, op2=None):
    """Construct the memory words using InstructionWord class

        >>> from ply.lex import LexToken
        >>> class LT(LexToken):
        ...     def __init__(s, t, v, ln, lp=0):
        ...         s.type, s.value, s.lineno, s.lexpos = t, v, ln, lp

        >>> op = LT('OPCODE', 'mov', 1)
        >>> o1 = LT('NAME', 'ax', 1)
        >>> o2 = LT('NUMBER', 234, 1)
        >>> instruction_words(op, o1, o2)
        ((1, InstructionWord(2, 2, 8)), DataWord(234))
    """
    opname = opcode.value.upper()
    i_word = InstructionWord(OPCODES[opname])

    # zero-operand instructions
    if op1 is None:
        if opname in ('NOP', 'HALT'):
            return ((opcode.lineno, i_word),)

    # 1-operand instructions
    elif op2 is None:
        jumps = ('JE', 'JGE', 'JGT', 'JLE', 'JLT', 'JMP',
                 'JN', 'JNE', 'JNZ', 'JP', 'JT', 'JV', 'JZ',)
        others = ('DEC', 'INC', 'NOT',)
        # Jump instructions
        if opname in jumps:
            if op1.type == 'NAME':
                try:
                    i_word.operand = REGISTERS[op1.value.upper()]
                    i_word.flags = 0
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return ((opcode.lineno, i_word),)
            elif op1.type == 'REFERENCE':
                i_word.operand = op1.value
                i_word.flags = 1
                return ((opcode.lineno, i_word),)
            elif op1.type == 'NUMBER':
                i_word.flags = 2
                return ((opcode.lineno, i_word), DataWord(op1.value))
        # INC, DEC and NOT instructions
        elif opname in others:
            if op1.type == 'NAME':
                try:
                    i_word.operand = REGISTERS[op1.value.upper()]
                    i_word.flags = 0
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return ((opcode.lineno, i_word),)
            elif op1.type == 'REFERENCE':
                i_word.operand = op1.value
                i_word.flags = 1
                return ((opcode.lineno, i_word),)

    # 2-operand instructions
    else:
        shifts = ('SHR', 'SHL',)
        others = ('ADD', 'AND', 'CMP', 'ICMP', 'DIV', 'IADD', 'ICMP', 'IDIV',
            'IMOD', 'IMUL', 'ISUB', 'MOD', 'MOV', 'MUL', 'OR', 'SUB', 'XOR',)
        # Shift instructions
        if opname in shifts:
            if op2.type == 'NUMBER':
                if op1.type == 'NAME':
                    try:
                        i_word.operand = REGISTERS[op1.value.upper()]
                        i_word.flags = 0
                    except KeyError:
                        raise Exception("Error: bad register name '%s'" % \
                                e.args)

                    return ((opcode.lineno, i_word), DataWord(op2.value))
                elif op1.type == 'REFERENCE':
                    i_word.operand = op1.value
                    i_word.flags = 1
                    return ((opcode.lineno, i_word), DataWord(op2.value))
        # All other instructions
        elif opname in others:
            if op1.type == 'NAME' and op2.type == 'NAME':
                try:
                    i_word.operand = REGISTERS[op1.value.upper()] << 4
                    i_word.operand |= REGISTERS[op2.value.upper()]
                    i_word.flags = 0
                except KeyError, e:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return ((opcode.lineno, i_word),)
            elif op1.type == 'NAME' and op2.type == 'REFERENCE':
                try:
                    i_word.operand = REGISTERS[op1.value.upper()]
                    i_word.flags = 1
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return ((opcode.lineno, i_word), DataWord(op2.value))
            elif op1.type == 'NAME' and op2.type == 'NUMBER':
                try:
                    i_word.operand = REGISTERS[op1.value.upper()]
                    i_word.flags = 2
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return ((opcode.lineno, i_word), DataWord(op2.value))
            elif op1.type == 'REFERENCE' and op2.type == 'NAME':
                try:
                    i_word.operand = REGISTERS[op2.value.upper()]
                    i_word.flags = 3
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return ((opcode.lineno, i_word), DataWord(op1.value))

    return None
