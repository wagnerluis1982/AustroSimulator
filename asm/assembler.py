# Austro Simulator Assembler

# NOTE: This was intended to be a parser, but isn't due to lack of knowledge.

from asm.asm_lexer import lexer
from asm.memword import InstructionWord, DataWord


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


def memory_words(opcode, op1=None, op2=None):
    """Construct memory words using InstructionWord and DataWord classes

    The output of this function is a tuple of one or two elements.

    If compounded of one element, this element is a InstructionWord object.

    If compounded of two elements, then
    - first is a InstructionWord object and
    - second is a DataWord object.
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
                except KeyError, e:
                    raise Exception("Error: bad register name '%s'" % e.args)

                return (instr_word,)
            elif op1.type == 'REFERENCE':
                instr_word.operand = op1.value
                instr_word.flags = 1
                return (instr_word,)
            elif op1.type == 'NUMBER':
                instr_word.operand = op1.value
                instr_word.flags = 2
                return (instr_word,)

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
                'loop': 6,  # loop is a label and 1 the associated address
                'rept': 8,
                ...
            }
         'words': [
                InstructionWord(5, 7, 46, lineno=1),
                DataWord(2028),
                ...
            ]
        }

    As can be seen, the labels itself are another dict where the key is a
    label name and the value the following instruction associated address.

    The 'words' key is a mixed list of InstructionWord and DataWord objects,
    representing 16-bit words, intended to be a kind of Austro Simulator
    assembler.

    The InstructionWord object carry lineno attribute that is the associated
    line number in assembly file.
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
                if lbl.value in labels:
                    raise Exception("Error: symbol '%s' is already defined." %
                            lbl.value, lbl.lineno)
                # Point the label to the next word pending attribution
                labels[lbl.value] = len(words)
                del lbl

            # Store opcode
            opcode = tok

            # Get first operator if available
            tok = lexer.token()
            if not tok or tok.lineno != opcode.lineno:
                words.extend(memory_words(opcode))  # non-arg opcode
                continue
            op1 = tok

            # Comma
            tok = lexer.token()
            if not tok or tok.lineno != opcode.lineno:
                # If instruction is a jump, replace labels by it address
                jumps = ('JE', 'JGE', 'JGT', 'JLE', 'JLT', 'JMP',
                         'JN', 'JNE', 'JNZ', 'JP', 'JT', 'JV', 'JZ',)
                if op1.type == 'NAME' and opcode.value.upper() in jumps:
                    if op1.value not in labels:
                        raise Exception("Invalid label '%s'" % op1.value,
                                op1.lineno)
                    op1.type = 'NUMBER'
                    op1.value = labels[op1.value]

                words.extend(memory_words(opcode, op1))  # 1-arg opcode
                continue
            if tok.type != 'COMMA':
                raise Exception("Invalid token", tok.lineno)

            # Get second operator if available
            tok = lexer.token()
            if not tok or tok.lineno != opcode.lineno:
                raise Exception("Invalid syntax", opcode.lineno)
            op2 = tok

            words.extend(memory_words(opcode, op1, op2))  # 2-arg opcode

        # At start of line, only labels and opcodes are allowed
        else:
            raise Exception("Invalid token", tok.lineno)

        tok = lexer.token()

    return {'labels': labels, 'words': words}


def main():
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


if __name__ == "__main__":
    main()
