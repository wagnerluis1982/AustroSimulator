from austro.asm.assembler import assemble
from austro.simulator.cpu import CPU, Registers, StepEvent


#
## The cpu receives at start a StepEvent class instance. Here two simple examples:
#
class ShowRegistersEvent(StepEvent):
    def __init__(self, *names):
        self.messages = []
        self.fmt = ','.join(['%s=%%d' % nm for nm in names])

        self.indexes = []
        for nm in names:
            self.indexes.append(Registers.INDEX[nm])

    def on_fetch(self):
        args = [self.cpu.registers[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


class ShowMemoriesEvent(StepEvent):
    def __init__(self, *numbers):
        self.messages = []
        self.fmt = ','.join(['[%d]=%%d' % n for n in numbers])
        self.indexes = numbers

    def on_fetch(self):
        args = [self.cpu.memory[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


def assert_registers(assembly, registers, messages):
    # instructions
    asmd = assemble(assembly)

    event = ShowRegistersEvent(*registers)
    cpu = CPU(event)
    cpu.set_memory_block(asmd['words'])

    # Test run
    assert cpu.start() is True

    # Test step event
    assert event.messages == messages


def assert_memory(assembly, addresses, messages):
    # instructions
    asmd = assemble(assembly)

    event = ShowMemoriesEvent(*addresses)
    cpu = CPU(event)
    cpu.set_memory_block(asmd['words'])

    # Test run
    assert cpu.start() is True

    # Test step event
    assert event.messages == messages


class TestCPU__ALU:
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
        messages = ['AX=0,BX=0',    # before "mov ax, 0b1001"
                    'AX=9,BX=0',    # before "mov bx, 0b1100"
                    'AX=9,BX=12',   # before "or ax, bx"
                    'AX=13,BX=12']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0',  # before "mov ax, 0"
                    'Z=0',  # before "or ax, 1"
                    'Z=0',  # before "mov ax, 0"
                    'Z=0',  # before "or ax, 0"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',   # before "mov ax, 0b1100"
                    'AX=12,BX=0',  # before "mov bx, 0b0110"
                    'AX=12,BX=6',  # before "and ax, bx"
                    'AX=4,BX=6']   # before "halt"

        assert_registers(assembly, registers, messages)

    def test_and__flags(self):
        '''AND should set flag Z'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "and ax, 0\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # before "mov ax, 1"
                    'Z=0',  # before "and ax, 0"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_not(self):
        '''NOT should invert all bits of a value'''

        # instructions
        assembly = ("mov ax, 0xabcd\n"
                    "not ax\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',            # before "mov ax, 0xabcd"
                    'AX=%d' % 0xabcd,  # before "not ax"
                    'AX=%d' % 0x5432]  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_not__flags(self):
        '''NOT should set flag Z'''

        # instructions
        assembly = ("mov ax, 0xffff\n"
                    "not ax\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # before "mov ax, 0xffff"
                    'Z=0',  # before "not ax"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',    # before "mov ax, 0b1100"
                    'AX=12,BX=0',   # before "mov bx, 0b1010"
                    'AX=12,BX=10',  # before "xor ax, bx"
                    'AX=6,BX=10']   # before "halt"

        assert_registers(assembly, registers, messages)

    def test_xor__flags(self):
        '''XOR should set flag Z'''

        # instructions
        assembly = ("mov ax, 1\n"
                    "xor ax, 1\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # before "mov ax, 1"
                    'Z=0',  # before "xor ax, 1"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',      # before "mov ax, 193"
                    'AX=193,BX=0',    # before "mov bx, 297"
                    'AX=193,BX=297',  # before "add ax, bx"
                    'AX=490,BX=297']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0,V=0',  # before "mov ax, 65534"
                    'Z=0,V=0',  # before "mov bx, 65535"
                    'Z=0,V=0',  # before "add ax, 1"
                    'Z=0,V=0',  # before "add ax, 1"
                    'Z=1,V=1',  # before "add bx, 2"
                    'Z=0,V=1',  # before "mov cl, 255"
                    'Z=0,V=1',  # before "add cl, 1"
                    'Z=1,V=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',    # before "mov ax, 19"
                    'AX=19,BX=0',   # before "mov bx, 10"
                    'AX=19,BX=10',  # before "sub ax, bx"
                    'AX=9,BX=10']   # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0,V=0',  # before "mov ax, 1"
                    'Z=0,V=0',  # before "mov bx, 1"
                    'Z=0,V=0',  # before "sub ax, 2"
                    'Z=0,V=1',  # before "sub bx, 1"
                    'Z=1,V=0',  # before "sub bx, 1"
                    'Z=0,V=1']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_inc(self):
        '''INC should increment one unit of a value'''

        # instructions
        assembly = ("mov ax, 9\n"
                    "inc ax\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',   # before "mov ax, 9"
                    'AX=9',   # before "inc ax"
                    'AX=10']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0,V=0',  # before "mov ax, 0xfffe"
                    'Z=0,V=0',  # before "inc ax"
                    'Z=0,V=0',  # before "inc ax"
                    'Z=1,V=1']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_dec(self):
        '''DEC should decrement one unit of a value'''

        # instructions
        assembly = ("mov ax, 100\n"
                    "dec ax\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',    # before "mov ax, 100"
                    'AX=100',  # before "dec ax"
                    'AX=99']   # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0,V=0',  # before "mov ax, 1"
                    'Z=0,V=0',  # before "dec ax"
                    'Z=1,V=0',  # before "dec ax"
                    'Z=0,V=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',   # before "mov ax, 12"
                    'AX=12,BX=0',  # before "mov bx, 5"
                    'AX=12,BX=5',  # before "mul ax, bx"
                    'AX=60,BX=5']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_mul__transport(self):
        '''MUL should transport excess to SP register'''

        # instructions
        assembly = ("mov ax, 500\n"
                    "mov sp, 8\n"
                    "mul ax, 1\n"
                    "mul ax, 850\n"
                    "halt\n")
        # registers
        registers = ('AX', 'SP')
        # expected messages
        messages = ['AX=0,SP=0',      # before "mov ax, 500"
                    'AX=500,SP=0',    # before "mov sp, 8"
                    'AX=500,SP=8',    # before "mul ax, 1"
                    'AX=500,SP=8',    # before "mul ax, 850"
                    'AX=31784,SP=6']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_mul__flags(self):
        '''MUL should set flags Z and T'''

        # instructions
        assembly = ("mov ax, 77\n"
                    "mul ax, 900\n"
                    "mul ax, 0\n"
                    "halt\n")
        # registers
        registers = ('Z', 'T')
        # expected messages
        messages = ['Z=0,T=0',  # before "mov ax, 77"
                    'Z=0,T=0',  # before "mul ax, 900"
                    'Z=0,T=1',  # before "mul ax, 0"
                    'Z=1,T=0']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_imul__flags(self):
        '''IMUL should set flags N, Z and V'''

        # instructions
        assembly = ("mov ax, 80\n"
                    "imul ax, -900\n"
                    "imul ax, 0\n"
                    "halt\n")
        # registers
        registers = ('N', 'Z', 'V')
        # expected messages
        messages = ['N=0,Z=0,V=0',  # before "mov ax, 80"
                    'N=0,Z=0,V=0',  # before "imul ax, -900"
                    'N=1,Z=0,V=1',  # before "imul ax, 0"
                    'N=0,Z=1,V=0']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',  # before "mov ax, 7"
                    'AX=7,BX=0',  # before "mov bx, 2"
                    'AX=7,BX=2',  # before "div ax, bx"
                    'AX=3,BX=2']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0',  # before "mov ax, 3"
                    'Z=0',  # before "div ax, 3"
                    'Z=0',  # before "div ax, 4"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['AX=0,BX=0',  # before "mov ax, 7"
                    'AX=7,BX=0',  # before "mov bx, 2"
                    'AX=7,BX=2',  # before "mod ax, bx"
                    'AX=1,BX=2']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_mod__flags(self):
        '''MOD should set flag Z'''

        # instructions
        assembly = ("mov ax, 9\n"
                    "mod ax, 3\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # before "mov ax, 9"
                    'Z=0',  # before "mod ax, 3"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['N=0,Z=0',  # before "mov ax, 5"
                    'N=0,Z=0',  # before "cmp ax, 5"
                    'N=0,Z=1',  # before "cmp ax, 6"
                    'N=1,Z=0',  # before "cmp ax, 4"
                    'N=0,Z=0']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['N=0,Z=0',  # before "mov ax, -7"
                    'N=0,Z=0',  # before "cmp ax, -7"
                    'N=0,Z=1',  # before "cmp ax, 2"
                    'N=1,Z=0',  # before "cmp ax, -15"
                    'N=0,Z=0']  # before "halt"

        assert_registers(assembly, registers, messages)


class TestCPU__UC:
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
        messages = ['AX=0,BX=0',  # before "mov ax, 3"
                    'AX=3,BX=0',  # before "mov bx, ax"
                    'AX=3,BX=3']  # before "halt"

        assert_registers(assembly, registers, messages)

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
                'AX=%d,AH=%d,AL=%d' % (0x0, 0x0, 0x0),       # "mov al, 0x9A"
                'AX=%d,AH=%d,AL=%d' % (0x009A, 0x00, 0x9A),  # "mov ah, 0x10"
                'AX=%d,AH=%d,AL=%d' % (0x109A, 0x10, 0x9A),  # "mov ax, 0x9F8D"
                'AX=%d,AH=%d,AL=%d' % (0x9F8D, 0x9F, 0x8D)]  # "halt"

        assert_registers(assembly, registers, messages)

    def test_mov__reg_const(self):
        '''MOV should load a register from a constant'''

        # mov instructions
        assembly = ("mov ax, 9\n"
                    "mov bx, 4\n"
                    "halt\n")
        # registers
        registers = ('AX', 'BX')
        # expected messages
        messages = ['AX=0,BX=0',  # before "mov ax, 9"
                    'AX=9,BX=0',  # before "mov bx, 4"
                    'AX=9,BX=4']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['BX=0',  # before "mov ax, 7"
                    'BX=0',  # before "mov [128], ax"
                    'BX=0',  # before "mov bx, [128]"
                    'BX=7']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_mov__mem_reg(self):
        '''MOV should load a memory position from a register'''

        # mov instructions
        assembly = ("mov ax, 5\n"
                    "mov [128], ax\n"
                    "halt\n")
        # memory addresses
        addresses = (128,)
        # expected messages
        messages = ['[128]=0',  # before "mov ax, 5"
                    '[128]=0',  # before "mov [128], ax"
                    '[128]=5']  # before "halt"

        assert_memory(assembly, addresses, messages)

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
        messages = ['PC=0',  # before "mov ax, 1"
                    'PC=2',  # before "dec ax"
                    'PC=3',  # before "jz detour"
                    'PC=2',  # before "dec ax"
                    'PC=3',  # before "jz detour"
                    'PC=4',  # before "cmp ax, 65535"
                    'PC=6',  # before "je detour"
                    'PC=2',  # before "dec ax"
                    'PC=3',  # before "jz detour"
                    'PC=4',  # before "cmp ax, 65535"
                    'PC=6',  # before "je detour"
                    'PC=7']  # before "halt"

        assert_registers(assembly, registers, messages)


class TestCPU__SHIFT:
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
        messages = ['AX=0',   # before "mov ax, 0b100"
                    'AX=4',   # before "shr ax, bx"
                    'AX=16']  # before "halt"

        assert_registers(assembly, registers, messages)

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
        messages = ['Z=0',  # before "mov ax, 0x4000"
                    'Z=0',  # before "shl ax, 1"
                    'Z=0',  # before "shl ax, 1"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_shr(self):
        '''SHR should shift right a value'''

        # instructions
        assembly = ("mov ax, 0b1000\n"
                    "shr ax, 2\n"
                    "halt\n")
        # registers
        registers = ('AX',)
        # expected messages
        messages = ['AX=0',  # before "mov ax, 0b100"
                    'AX=8',  # before "shr ax, bx"
                    'AX=2']  # before "halt"

        assert_registers(assembly, registers, messages)

    def test_shr__flags(self):
        '''SHR should set flag Z'''

        # instructions
        assembly = ("mov ax, 0x0001\n"
                    "shr ax, 1\n"
                    "halt\n")
        # registers
        registers = ('Z')
        # expected messages
        messages = ['Z=0',  # before "mov ax, 0x0001"
                    'Z=0',  # before "shr ax, 1"
                    'Z=1']  # before "halt"

        assert_registers(assembly, registers, messages)
