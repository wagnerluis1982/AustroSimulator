# Austro Simulator Assembler

# NOTE: This was intended to be a parser, but it isn't due to lack of knowledge.

import ctypes

from asm_lexer import lexer

class InstructionWord(ctypes.Structure):
    """Represent the memory instruction word

        >>> iw = InstructionWord(0b00001, 0b010, 0b00000011)
        >>> bin(iw.value)
        '0b101000000011'
    """
    _fields_ = [('opcode', ctypes.c_ubyte, 5),
                ('flags', ctypes.c_ubyte, 3),
                ('operand', ctypes.c_ubyte, 8)]

    def __init__(self, opcode=0, flags=0, operand=0, lineno=0):
        ctypes.Structure.__init__(self, opcode, flags, operand)
        self.lineno = lineno

    @property
    def value(self):
        return (self.opcode << 3 | self.flags) << 8 | self.operand

    def __repr__(self):
        return 'InstructionWord(%d, %d, %d, lineno=%d)' % (self.opcode,
                                        self.flags, self.operand, self.lineno)

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

        >>> op = LT('OPCODE', 'mov', ln=1)
        >>> o1 = LT('NAME', 'ax', ln=1)
        >>> o2 = LT('NUMBER', 234, ln=1)
        >>> instruction_words(op, o1, o2)
        (InstructionWord(2, 2, 8, lineno=1), DataWord(234))
    """
    opname = opcode.value.upper()
    try:
        instr_word = InstructionWord(OPCODES[opname], lineno=opcode.lineno)
    except KeyError:
        raise Exception("Invalid instruction '%s'" % opname, opcode.lineno)

    # zero-operand instructions
    if op1 is None:
        if opname in ('NOP', 'HALT'):
            return (instr_word,)

    # 1-operand instructions
    elif op2 is None:
        jumps = ('JE', 'JGE', 'JGT', 'JLE', 'JLT', 'JMP',
                 'JN', 'JNE', 'JNZ', 'JP', 'JT', 'JV', 'JZ',)
        others = ('DEC', 'INC', 'NOT',)
        # Jump instructions
        if opname in jumps:
            if op1.type == 'NAME':
                try:
                    instr_word.operand = REGISTERS[op1.value.upper()]
                    instr_word.flags = 0
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word,)
            elif op1.type == 'REFERENCE':
                instr_word.operand = op1.value
                instr_word.flags = 1
                return (instr_word,)
            elif op1.type == 'NUMBER':
                instr_word.flags = 2
                return (instr_word, DataWord(op1.value))
        # INC, DEC and NOT instructions
        elif opname in others:
            if op1.type == 'NAME':
                try:
                    instr_word.operand = REGISTERS[op1.value.upper()]
                    instr_word.flags = 0
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word,)
            elif op1.type == 'REFERENCE':
                instr_word.operand = op1.value
                instr_word.flags = 1
                return (instr_word,)

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
                        instr_word.operand = REGISTERS[op1.value.upper()]
                        instr_word.flags = 0
                    except KeyError:
                        raise Exception("Error: bad register name '%s'" % \
                                e.args)

                    return (instr_word, DataWord(op2.value))
                elif op1.type == 'REFERENCE':
                    instr_word.operand = op1.value
                    instr_word.flags = 1
                    return (instr_word, DataWord(op2.value))
        # All other instructions
        elif opname in others:
            if opname in ('IADD', 'ICMP', 'IDIV', 'IMOD', 'IMUL', 'ISUB',):
                instr_word.flags = 0b100  # signed instructions

            if op1.type == 'NAME' and op2.type == 'NAME':
                try:
                    instr_word.operand = REGISTERS[op1.value.upper()] << 4
                    instr_word.operand |= REGISTERS[op2.value.upper()]
                    # flag x00 - no needs to set
                except KeyError, e:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word,)
            elif op1.type == 'NAME' and op2.type == 'REFERENCE':
                try:
                    instr_word.operand = REGISTERS[op1.value.upper()]
                    instr_word.flags |= 0b001  # flag x01
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word, DataWord(op2.value))
            elif op1.type == 'NAME' and op2.type == 'NUMBER':
                try:
                    instr_word.operand = REGISTERS[op1.value.upper()]
                    instr_word.flags |= 0b010  # flag x10
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word, DataWord(op2.value))
            elif op1.type == 'REFERENCE' and op2.type == 'NAME':
                try:
                    instr_word.operand = REGISTERS[op2.value.upper()]
                    instr_word.flags |= 0b011  # flag x11
                except KeyError:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word, DataWord(op1.value))

    return None


def assemble(code):
    """Analyzes assembly code and returns a dict of labels and memory words

    The returned dict is in the following format:

        {'labels': {
                'loop': 1,  # loop is a label and 1 the associated address
                'rept': 2,
                ...
            }
         'words': [
                (1, InstructionWord(5, 7, 46)),
                DataWord(2028),
                ...
            ]
        }

    As can be seen, the labels itself are another dict where the key is a
    label name and the value the following instruction associated address.

    The 'words' key is a mixed list of tuples representing 16-bit words, that is
    intended to be a kind of Austro Simulator assembler, and int values
    representing data operand-only words.

    The tuples are instruction words in the following format:

        (line, opcode, flags, operand,)

    where line is the associated line number in the assembly file.
    """
    lexer.input(code)

    # Structures to store labels and memory words
    labels = {}
    words = []

    opcode = None
    pend_labels = []
    tok = lexer.token()
    while tok:
        if tok.type == 'LABEL':
            pend_labels.append(tok)

        elif tok.type == 'OPCODE':
            # Verify if has any label pending an address
            while pend_labels:
                lbl = pend_labels.pop()
                if labels.has_key(lbl.value):
                    raise Exception("Error: symbol '%s' is already defined." % \
                            lbl.value, lbl.lineno)
                # Point the label to the next word pending attribution
                labels[lbl.value] = len(words)
                del lbl

            # Store opcode
            opcode = tok

            # Get first operator if available
            tok = lexer.token()
            if tok.lineno != opcode.lineno:
                words.extend(instruction_words(opcode))  # non-arg opcode
                continue
            op1 = tok

            # Comma
            tok = lexer.token()
            if tok.lineno != opcode.lineno:
                words.extend(instruction_words(opcode, op1))  # 1-arg opcode
                continue
            elif tok.type != 'COMMA':
                raise Exception("Invalid token", tok.lineno)

            # Get second operator if available
            tok = lexer.token()
            if tok.lineno != opcode.lineno:
                raise Exception("Invalid syntax", opcode.lineno)
            op2 = tok

            words.extend(instruction_words(opcode, op1, op2))  # 2-arg opcode

        # At start of line, only labels and opcodes are allowed
        else:
            raise Exception("Invalid token", tok.lineno)

        tok = lexer.token()

    return {'labels': labels, 'words': words}


if __name__ == "__main__":
    import sys
    import os
    try:
        filename = sys.argv[1]
        f = open(filename)
        data = f.read()
        f.close()
    except IndexError:
        data = sys.stdin.read()

    from pprint import pprint
    pprint(assemble(data))
