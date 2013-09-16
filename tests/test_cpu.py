import unittest

from asm.assembler import assemble
from simulator.cpu import CPU, Registers, Step

#
## The cpu receives at start a Step class instance. Here two simple examples:
#
class ShowRegisters(Step):
    def __init__(self, *names):
        self.messages = []
        self.fmt = ','.join(['%s=%%d' % nm for nm in names])

        self.indexes = []
        for nm in names:
            self.indexes.append(Registers.INDEX[nm])

    def do(self):
        args = [self.cpu.registers[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


class ShowMemories(Step):
    def __init__(self, *numbers):
        self.messages = []
        self.fmt = ','.join(['[%d]=%%d' % n for n in numbers])
        self.indexes = numbers

    def do(self):
        args = [self.cpu.memory[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


class CPUTestCase(unittest.TestCase):
    def register_asserts(self, assembly, registers, messages):
        # instructions
        asmd = assemble(assembly)

        cpu = CPU()
        cpu.set_memory_block(asmd['words'])

        # Test run
        show = ShowRegisters(*registers)
        self.assertTrue( cpu.start(show) )

        # Test step
        self.assertEqual( show.messages, messages )

    def memory_asserts(self, assembly, addresses, messages):
        # instructions
        asmd = assemble(assembly)

        cpu = CPU()
        cpu.set_memory_block(asmd['words'])

        # Test run
        show = ShowMemories(*addresses)
        self.assertTrue( cpu.start(show) )

        # Test step
        self.assertEqual( show.messages, messages )


class TestCPU__ALU(CPUTestCase):
    '''CPU (Arithmetic and Logic Unit)'''

    def test_or__reg_reg(self):
        '''OR should do a bitwise OR on two registers'''

        # instructions
        assembly = ("mov ax, 0b1001\n"
                    "mov bx, 0b1100\n"
                    "or ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',    # start
                    'AX=9,BX=0',    # after "mov ax, 0b1001"
                    'AX=9,BX=12',   # after "mov bx, 0b1100"
                    'AX=13,BX=12',  # after "or ax, bx"
                    'AX=13,BX=12']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_or__flags(self):
        '''OR should set flag Z'''

        # instructions
        assembly = ("mov ax, 0\n"
                    "or ax, 1\n"
                    "mov ax, 0\n"
                    "or ax, 0\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 0"
                    'Z=0',  # after "or ax, 1"
                    'Z=0',  # after "mov ax, 0"
                    'Z=1',  # after "or ax, 0"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_and__reg_reg(self):
        '''AND should do a bitwise AND on two registers'''

        # instructions
        assembly = ("mov ax, 0b1100\n"
                    "mov bx, 0b0110\n"
                    "and ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',   # start
                    'AX=12,BX=0',  # after "mov ax, 0b1100"
                    'AX=12,BX=6',  # after "mov bx, 0b0110"
                    'AX=4,BX=6',   # after "and ax, bx"
                    'AX=4,BX=6']   # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_and__flags(self):
        '''AND should set flag Z'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "and ax, 0\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 1"
                    'Z=1',  # after "and ax, 0"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_not(self):
        '''NOT should invert all bits of a value'''

        # instructions
        assembly = ("mov ax, 0xabcd\n"
                    "not ax\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',            # start
                    'AX=%d' % 0xabcd,  # after "mov ax, 0xabcd"
                    'AX=%d' % 0x5432,  # after "not ax"
                    'AX=%d' % 0x5432]  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_not__flags(self):
        '''NOT should set flag Z'''

        # instructions
        assembly = ("mov ax, 0xffff\n"
                    "not ax\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 0xffff"
                    'Z=1',  # after "not ax"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_xor__reg_reg(self):
        '''XOR should do a bitwise XOR on two registers'''

        # instructions
        assembly = ("mov ax, 0b1100\n"
                    "mov bx, 0b1010\n"
                    "xor ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',    # start
                    'AX=12,BX=0',   # after "mov ax, 0b1100"
                    'AX=12,BX=10',  # after "mov bx, 0b1010"
                    'AX=6,BX=10',   # after "xor ax, bx"
                    'AX=6,BX=10']   # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_xor__flags(self):
        '''XOR should set flag Z'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "xor ax, 1\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 1"
                    'Z=1',  # after "xor ax, 1"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_add__reg_reg(self):
        '''ADD should sum two registers'''

        # instructions
        assembly = ("mov ax, 193\n"
                    "mov bx, 297\n"
                    "add ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',      # start
                    'AX=193,BX=0',    # after "mov ax, 193"
                    'AX=193,BX=297',  # after "mov bx, 297"
                    'AX=490,BX=297',  # after "add ax, bx"
                    'AX=490,BX=297']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_add__flags(self):
        '''ADD should set flags Z and V'''

        # instructions
        assembly = ("mov ax, 65534\n"
                    "mov bx, 65535\n"
                    "add ax, 1\n"
                    "add ax, 1\n"
                    "add bx, 2\n"
                    "mov cl, 255\n"
                    "add cl, 1\n"
                    "halt\n")
        # registers
        registers = ('Z', 'V')
        # expected messages
        messages = ['Z=0,V=0',  # start
                    'Z=0,V=0',  # after "mov ax, 65534"
                    'Z=0,V=0',  # after "mov bx, 65535"
                    'Z=0,V=0',  # after "add ax, 1"
                    'Z=1,V=1',  # after "add ax, 1"
                    'Z=0,V=1',  # after "add bx, 2"
                    'Z=0,V=1',  # after "mov cl, 255"
                    'Z=1,V=1',  # after "add cl, 1"
                    'Z=1,V=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_sub__reg_reg(self):
        '''SUB should subtract two registers'''

        # instructions
        assembly = ("mov ax, 19\n"
                    "mov bx, 10\n"
                    "sub ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',   # start
                    'AX=19,BX=0',  # after "mov ax, 19"
                    'AX=19,BX=10', # after "mov bx, 10"
                    'AX=9,BX=10',  # after "sub ax, bx"
                    'AX=9,BX=10']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_sub__flags(self):
        '''SUB should set flags Z and V'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "mov bx, 1\n"
                    "sub ax, 2\n"
                    "sub bx, 1\n"
                    "sub bx, 1\n"
                    "halt\n")
        # registers
        registers = ('Z', 'V')
        # expected messages
        messages = ['Z=0,V=0',  # start
                    'Z=0,V=0',  # after "mov ax, 1"
                    'Z=0,V=0',  # after "mov bx, 1"
                    'Z=0,V=1',  # after "sub ax, 2"
                    'Z=1,V=0',  # after "sub bx, 1"
                    'Z=0,V=1',  # after "sub bx, 1"
                    'Z=0,V=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_inc(self):
        '''INC should increment one unit of a value'''

        # instructions
        assembly = ("mov ax, 9\n"
                    "inc ax\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',   # start
                    'AX=9',   # after "mov ax, 9"
                    'AX=10',  # after "inc ax"
                    'AX=10']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_inc__flags(self):
        '''INC should set flags Z and V'''

        # instructions
        assembly = ("mov ax, 0xfffe\n"
                    "inc ax\n"
                    "inc ax\n"
                    "halt\n")
        # registers
        registers = ('Z', 'V')
        # expected messages
        messages = ['Z=0,V=0',  # start
                    'Z=0,V=0',  # after "mov ax, 0xfffe"
                    'Z=0,V=0',  # after "inc ax"
                    'Z=1,V=1',  # after "inc ax"
                    'Z=1,V=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_dec(self):
        '''DEC should decrement one unit of a value'''

        # instructions
        assembly = ("mov ax, 100\n"
                    "dec ax\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',    # start
                    'AX=100',  # after "mov ax, 100"
                    'AX=99',   # after "dec ax"
                    'AX=99']   # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_dec__flags(self):
        '''DEC should set flags Z and V'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "dec ax\n"
                    "dec ax\n"
                    "halt\n")
        # registers
        registers = ('Z', 'V')
        # expected messages
        messages = ['Z=0,V=0',  # start
                    'Z=0,V=0',  # after "mov ax, 1"
                    'Z=1,V=0',  # after "dec ax"
                    'Z=0,V=1',  # after "dec ax"
                    'Z=0,V=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mul__reg_reg(self):
        '''MUL should multiply two registers'''

        # instructions
        assembly = ("mov ax, 12\n"
                    "mov bx, 5\n"
                    "mul ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',   # start
                    'AX=12,BX=0',  # after "mov ax, 12"
                    'AX=12,BX=5',  # after "mov bx, 5"
                    'AX=60,BX=5',  # after "mul ax, bx"
                    'AX=60,BX=5']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mul__flags(self):
        '''MUL should set flag Z'''

        # instructions
        assembly = ("mov ax, 77\n"
                    "mul ax, 0\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 77"
                    'Z=1',  # after "mul ax, 0"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_div__reg_reg(self):
        '''DIV should calculate quotient of two registers'''

        # instructions
        assembly = ("mov ax, 7\n"
                    "mov bx, 2\n"
                    "div ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',  # start
                    'AX=7,BX=0',  # after "mov ax, 7"
                    'AX=7,BX=2',  # after "mov bx, 2"
                    'AX=3,BX=2',  # after "div ax, bx"
                    'AX=3,BX=2']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_div__flags(self):
        '''DIV should set flag Z'''

        # instructions
        assembly = ("mov ax, 3\n"
                    "div ax, 3\n"
                    "div ax, 4\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 3"
                    'Z=0',  # after "div ax, 3"
                    'Z=1',  # after "div ax, 4"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mod__reg_reg(self):
        '''MOD should calculate remainder of two registers'''

        # instructions
        assembly = ("mov ax, 7\n"
                    "mov bx, 2\n"
                    "mod ax, bx\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',    # start
                    'AX=7,BX=0',    # after "mov ax, 7"
                    'AX=7,BX=2',    # after "mov bx, 2"
                    'AX=1,BX=2',    # after "mod ax, bx"
                    'AX=1,BX=2']    # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mod__flags(self):
        '''MOD should set flag Z'''

        # instructions
        assembly = ("mov ax, 9\n"
                    "mod ax, 3\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 9"
                    'Z=1',  # after "mod ax, 3"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_cmp(self):
        '''CMP should compare two values and set flags N and Z'''

        # instructions
        assembly = ("mov ax, 5\n"
                    "cmp ax, 5\n"
                    "cmp ax, 6\n"
                    "cmp ax, 4\n"
                    "halt\n")
        # registers
        registers = ('N', 'Z')
        # expected messages
        messages = ['N=0,Z=0',  # start
                    'N=0,Z=0',  # after "mov ax, 5"
                    'N=0,Z=1',  # after "cmp ax, 5"
                    'N=1,Z=0',  # after "cmp ax, 6"
                    'N=0,Z=0',  # after "cmp ax, 4"
                    'N=0,Z=0']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_icmp(self):
        '''ICMP should signed compare two values and set flags N and Z'''

        # instructions
        assembly = ("mov ax, -7\n"
                    "icmp ax, -7\n"
                    "icmp ax, 2\n"
                    "icmp ax, -15\n"
                    "halt\n")
        # registers
        registers = ('N', 'Z')
        # expected messages
        messages = ['N=0,Z=0',  # start
                    'N=0,Z=0',  # after "mov ax, -7"
                    'N=0,Z=1',  # after "cmp ax, -7"
                    'N=1,Z=0',  # after "cmp ax, 2"
                    'N=0,Z=0',  # after "cmp ax, -15"
                    'N=0,Z=0']  # after "halt"

        self.register_asserts(assembly, registers, messages)


class TestCPU__UC(CPUTestCase):
    '''CPU (Control Unit)'''

    def test_mov__reg_reg(self):
        '''MOV should load a register from another register'''

        # mov instructions
        assembly = ("mov ax, 3\n"
                    "mov bx, ax\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',  # start
                    'AX=3,BX=0',  # after "mov ax, 3"
                    'AX=3,BX=3',  # after "mov bx, ax"
                    'AX=3,BX=3']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__high_low(self):
        '''MOV should allow setting most and less significant register areas'''

        # mov instructions
        assembly = ("mov al, 0x9A\n"
                    "mov ah, 0x10\n"
                    "mov ax, 0x9F8D\n"
                    "halt\n")
        # registers
        registers = ('AX', 'AH', 'AL')
        # expected messages
        messages = [
                'AX=%d,AH=%d,AL=%d' % (0x0, 0x0, 0x0),  # start
                'AX=%d,AH=%d,AL=%d' % (0x009A, 0x00, 0x9A),  # "mov al, 0x9A"
                'AX=%d,AH=%d,AL=%d' % (0x109A, 0x10, 0x9A),  # "mov ah, 0x10"
                'AX=%d,AH=%d,AL=%d' % (0x9F8D, 0x9F, 0x8D),  # "mov ax, 0x9F8D"
                'AX=%d,AH=%d,AL=%d' % (0x9F8D, 0x9F, 0x8D)]  # "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__reg_const(self):
        '''MOV should load a register from a constant'''

        # mov instructions
        assembly = ("mov ax, 9\n"
                    "mov bx, 4\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',  # start
                    'AX=9,BX=0',  # after "mov ax, 9"
                    'AX=9,BX=4',  # after "mov bx, 4"
                    'AX=9,BX=4']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__reg_mem(self):
        '''MOV should load a register from a memory position'''

        # mov instructions
        assembly = ("mov ax, 7\n"
                    "mov [128], ax\n"
                    "mov bx, [128]\n"
                    "halt\n")
        # registers
        registers = ('BX',)
        # expected messages
        messages = ['BX=0',  # start
                    'BX=0',  # after "mov ax, 7"
                    'BX=0',  # after "mov [128], ax"
                    'BX=7',  # after "mov bx, [128]"
                    'BX=7']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_mov__mem_reg(self):
        '''MOV should load a memory position from a register'''

        # mov instructions
        assembly = ("mov ax, 5\n"
                    "mov [128], ax\n"
                    "halt\n")
        # memory addresses
        memories = (128,)
        # expected messages
        messages = ['[128]=0',  # start
                    '[128]=0',  # after "mov ax, 5"
                    '[128]=5',  # after "mov [128], ax"
                    '[128]=5']  # after "halt"

        self.memory_asserts(assembly, memories, messages)

    def test_jz_je(self):
        '''JZ/JE should set PC register when Z=1'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "detour:\n"
                    "dec ax\n"
                    "jz detour\n"
                    "cmp ax, 65535\n"
                    "je detour\n"
                    "halt\n")
        # registers
        registers = ('PC',)
        # expected messages
        messages = ['PC=0',  # start
                    'PC=2',  # after "mov ax, 1"
                    'PC=3',  # after "dec ax"
                    'PC=2',  # after "jz detour"
                    'PC=3',  # after "dec ax"
                    'PC=4',  # after "jz detour"
                    'PC=6',  # after "cmp ax, 65535"
                    'PC=2',  # after "je detour"
                    'PC=3',  # after "dec ax"
                    'PC=4',  # after "jz detour"
                    'PC=6',  # after "cmp ax, 65535"
                    'PC=7',  # after "je detour"
                    'PC=7']  # after "halt"

        self.register_asserts(assembly, registers, messages)


class TestCPU__SHIFT(CPUTestCase):
    '''CPU (Shift Unit)'''

    def test_shl(self):
        '''SHL should shift left a value'''

        # instructions
        assembly = ("mov ax, 0b100\n"
                    "shl ax, 2\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',   # start
                    'AX=4',   # after "mov ax, 0b100"
                    'AX=16',  # after "shr ax, bx"
                    'AX=16']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_shl__flags(self):
        '''SHL should set flag Z'''

        # instructions
        assembly = ("mov ax, 0x4000\n"
                    "shl ax, 1\n"
                    "shl ax, 1\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 0x4000"
                    'Z=0',  # after "shl ax, 1"
                    'Z=1',  # after "shl ax, 1"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_shr(self):
        '''SHR should shift right a value'''

        # instructions
        assembly = ("mov ax, 0b1000\n"
                    "shr ax, 2\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',  # start
                    'AX=8',  # after "mov ax, 0b100"
                    'AX=2',  # after "shr ax, bx"
                    'AX=2']  # after "halt"

        self.register_asserts(assembly, registers, messages)

    def test_shr__flags(self):
        '''SHR should set flag Z'''

        # instructions
        assembly = ("mov ax, 0x0001\n"
                    "shr ax, 1\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # start
                    'Z=0',  # after "mov ax, 0x0001"
                    'Z=1',  # after "shr ax, 1"
                    'Z=1']  # after "halt"

        self.register_asserts(assembly, registers, messages)
