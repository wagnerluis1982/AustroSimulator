from __future__ import annotations

from typing import override

import pytest

from austro.asm.assembler import assemble
from austro.asm.memword import DWord
from austro.simulator.cpu import CPU, CPUException, Registers, Stage, StepListener


class ShowRegisters(StepListener):
    def __init__(self, *names: str) -> None:
        self.messages: list[str] = []
        self.fmt = ",".join(["%s=%%d" % nm for nm in names])

        self.indexes = []
        for nm in names:
            self.indexes.append(Registers.INDEX[nm])

    @override
    def on_fetch(self, registers, memory) -> None:
        args = [registers[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


class ShowMemories(StepListener):
    def __init__(self, *numbers: int) -> None:
        self.messages: list[str] = []
        self.fmt = ",".join(["[%d]=%%d" % n for n in numbers])
        self.indexes = numbers

    @override
    def on_fetch(self, registers, memory) -> None:
        args = [memory[i] for i in self.indexes]
        self.messages.append(self.fmt % tuple(args))


@pytest.fixture
def cpu():
    return CPU()


def assert_registers(assembly, registers, messages):
    # instructions
    asmd = assemble(assembly)

    listener = ShowRegisters(*registers)
    cpu = CPU(listener)
    cpu.set_memory_block(asmd["words"])

    # Test run
    assert cpu.start() is True

    # Test captured history
    assert listener.messages == messages


def assert_memory(assembly, addresses, messages):
    # instructions
    asmd = assemble(assembly)

    listener = ShowMemories(*addresses)
    cpu = CPU(listener)
    cpu.set_memory_block(asmd["words"])

    # Test run
    assert cpu.start() is True

    # Test captured history
    assert listener.messages == messages


class TestCPU:
    """CPU"""

    def test_start_with_cpu_stopped(self, cpu: CPU):
        cpu.stop()

        assert cpu.start() is False

    def test_next_with_cpu_stopped(self, cpu: CPU):
        cpu.stop()

        assert next(cpu) is False

    def test_reset(self, cpu: CPU):
        cpu.stage = Stage.FETCH
        cpu.registers["AX"] = 99
        cpu.set_memory_block(
            [
                DWord(1),
                DWord(2),
                DWord(3),
            ]
        )

        cpu.reset()

        assert cpu.stage == Stage.INITIAL
        assert all(w.value == 0 for _, w in cpu.memory)
        assert all(r.value == 0 for _, r in cpu.registers)

    def test_error_next_with_register_pc_greater_than_address_space(self, cpu: CPU):
        cpu.stage = Stage.FETCH
        cpu.registers["PC"] = CPU.ADDRESS_SPACE

        with pytest.raises(CPUException, match="PC register greater than address space"):
            next(cpu)

    def test_error_set_memory_block_greater_than_address_space(self, cpu: CPU):
        block = [DWord()] * (CPU.ADDRESS_SPACE + 1)
        with pytest.raises(CPUException, match="tried to set memory to outside address space"):
            cpu.set_memory_block(block)


class TestCPU__ALU:
    """CPU (Arithmetic and Logic Unit)"""

    def test_or__reg_reg(self):
        """OR should perform a bitwise OR on two registers"""

        # instructions
        assembly = """
            mov ax, 0b1001
            mov bx, 0b1100
            or ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 0b1001"
            "AX=0,BX=0",
            # before "mov bx, 0b1100"
            "AX=9,BX=0",
            # before "or ax, bx"
            "AX=9,BX=12",
            # AX = 0b1001 & 0b1100 => 0b1101 => 13
            "AX=13,BX=12",
        ]

        assert_registers(assembly, registers, messages)

    def test_or__flags(self):
        """OR should set flag Z"""

        # instructions
        assembly = """
            mov ax, 0
            or ax, 1
            mov ax, 0
            or ax, 0
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 0"
            "Z=0",
            # before "or ax, 1"
            "Z=0",
            # before "mov ax, 0"
            "Z=0",
            # before "or ax, 0"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_and__reg_reg(self):
        """AND should do a bitwise AND on two registers"""

        # instructions
        assembly = """
            mov ax, 0b1100
            mov bx, 0b0110
            and ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 0b1100"
            "AX=0,BX=0",
            # before "mov bx, 0b0110"
            "AX=12,BX=0",
            # before "and ax, bx"
            "AX=12,BX=6",
            # before "halt"
            "AX=4,BX=6",
        ]

        assert_registers(assembly, registers, messages)

    def test_and__flags(self):
        """AND should set flag Z"""

        # instructions
        assembly = """
            mov ax, 1
            and ax, 0
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 1"
            "Z=0",
            # before "and ax, 0"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_not(self):
        """NOT should invert all bits of a value"""

        # instructions
        assembly = """
            mov ax, 0xabcd
            not ax
            halt
        """
        # registers
        registers = ("AX",)
        # expected messages
        messages = [
            # before "mov ax, 0xabcd"
            "AX=0",
            # before "not ax"
            "AX=%d" % 0xABCD,
            # before "halt"
            "AX=%d" % 0x5432,
        ]

        assert_registers(assembly, registers, messages)

    def test_not__flags(self):
        """NOT should set flag Z"""

        # instructions
        assembly = """
            mov ax, 0xffff
            not ax
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 0xffff"
            "Z=0",
            # before "not ax"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_xor__reg_reg(self):
        """XOR should do a bitwise XOR on two registers"""

        # instructions
        assembly = """
            mov ax, 0b1100
            mov bx, 0b1010
            xor ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 0b1100"
            "AX=0,BX=0",
            # before "mov bx, 0b1010"
            "AX=12,BX=0",
            # before "xor ax, bx"
            "AX=12,BX=10",
            # before "halt"
            "AX=6,BX=10",
        ]

        assert_registers(assembly, registers, messages)

    def test_xor__flags(self):
        """XOR should set flag Z"""

        # instructions
        assembly = """
            mov ax, 1
            xor ax, 1
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 1"
            "Z=0",
            # before "xor ax, 1"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_add__reg_reg(self):
        """ADD should sum two registers"""

        # instructions
        assembly = """
            mov ax, 193
            mov bx, 297
            add ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 193"
            "AX=0,BX=0",
            # before "mov bx, 297"
            "AX=193,BX=0",
            # before "add ax, bx"
            "AX=193,BX=297",
            # before "halt"
            "AX=490,BX=297",
        ]

        assert_registers(assembly, registers, messages)

    def test_add__flags(self):
        """ADD should set flags Z and V"""

        # instructions
        assembly = (
            "mov ax, 65534\n"
            "mov bx, 65535\n"
            "add ax, 1\n"
            "add ax, 1\n"
            "add bx, 2\n"
            "mov cl, 255\n"
            "add cl, 1\n"
            "halt\n"
        )
        # registers
        registers = ("Z", "V")
        # expected messages
        messages = [
            # before "mov ax, 65534"
            "Z=0,V=0",
            # before "mov bx, 65535"
            "Z=0,V=0",
            # before "add ax, 1"
            "Z=0,V=0",
            # before "add ax, 1"
            "Z=0,V=0",
            # before "add bx, 2"
            "Z=1,V=1",
            # before "mov cl, 255"
            "Z=0,V=1",
            # before "add cl, 1"
            "Z=0,V=1",
            # before "halt"
            "Z=1,V=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_sub__reg_reg(self):
        """SUB should subtract two registers"""

        # instructions
        assembly = """
            mov ax, 19
            mov bx, 10
            sub ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 19"
            "AX=0,BX=0",
            # before "mov bx, 10"
            "AX=19,BX=0",
            # before "sub ax, bx"
            "AX=19,BX=10",
            # before "halt"
            "AX=9,BX=10",
        ]

        assert_registers(assembly, registers, messages)

    def test_sub__flags(self):
        """SUB should set flags Z and V"""

        # instructions
        assembly = """
            mov ax, 1
            mov bx, 1
            sub ax, 2
            sub bx, 1
            sub bx, 1
            halt
        """
        # registers
        registers = ("Z", "V")
        # expected messages
        messages = [
            # before "mov ax, 1"
            "Z=0,V=0",
            # before "mov bx, 1"
            "Z=0,V=0",
            # before "sub ax, 2"
            "Z=0,V=0",
            # before "sub bx, 1"
            "Z=0,V=1",
            # before "sub bx, 1"
            "Z=1,V=0",
            # before "halt"
            "Z=0,V=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_inc(self):
        """INC should increment one unit of a value"""

        # instructions
        assembly = """
            mov ax, 9
            inc ax
            halt
        """
        # registers
        registers = ("AX",)
        # expected messages
        messages = [
            # before "mov ax, 9"
            "AX=0",
            # before "inc ax"
            "AX=9",
            # before "halt"
            "AX=10",
        ]

        assert_registers(assembly, registers, messages)

    def test_inc__flags(self):
        """INC should set flags Z and V"""

        # instructions
        assembly = """
            mov ax, 0xfffe
            inc ax
            inc ax
            halt
        """
        # registers
        registers = ("Z", "V")
        # expected messages
        messages = [
            # before "mov ax, 0xfffe"
            "Z=0,V=0",
            # before "inc ax"
            "Z=0,V=0",
            # before "inc ax"
            "Z=0,V=0",
            # before "halt"
            "Z=1,V=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_dec(self):
        """DEC should decrement one unit of a value"""

        # instructions
        assembly = """
            mov ax, 100
            dec ax
            halt
        """
        # registers
        registers = ("AX",)
        # expected messages
        messages = [
            # before "mov ax, 100"
            "AX=0",
            # before "dec ax"
            "AX=100",
            # before "halt"
            "AX=99",
        ]

        assert_registers(assembly, registers, messages)

    def test_dec__flags(self):
        """DEC should set flags Z and V"""

        # instructions
        assembly = """
            mov ax, 1
            dec ax
            dec ax
            halt
        """
        # registers
        registers = ("Z", "V")
        # expected messages
        messages = [
            # before "mov ax, 1"
            "Z=0,V=0",
            # before "dec ax"
            "Z=0,V=0",
            # before "dec ax"
            "Z=1,V=0",
            # before "halt"
            "Z=0,V=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_mul__reg_reg(self):
        """MUL should multiply two registers"""

        # instructions
        assembly = """
            mov ax, 12
            mov bx, 5
            mul ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 12"
            "AX=0,BX=0",
            # before "mov bx, 5"
            "AX=12,BX=0",
            # before "mul ax, bx"
            "AX=12,BX=5",
            # before "halt"
            "AX=60,BX=5",
        ]

        assert_registers(assembly, registers, messages)

    def test_mul__transport(self):
        """MUL should transport excess to SP register"""

        # instructions
        assembly = """
            mov ax, 500
            mov sp, 8
            mul ax, 1
            mul ax, 850
            halt
        """
        # registers
        registers = ("AX", "SP")
        # expected messages
        messages = [
            # before "mov ax, 500"
            "AX=0,SP=0",
            # before "mov sp, 8"
            "AX=500,SP=0",
            # before "mul ax, 1"
            "AX=500,SP=8",
            # before "mul ax, 850"
            "AX=500,SP=8",
            # before "halt"
            "AX=31784,SP=6",
        ]

        assert_registers(assembly, registers, messages)

    def test_mul__flags(self):
        """MUL should set flags Z and T"""

        # instructions
        assembly = """
            mov ax, 77
            mul ax, 900
            mul ax, 0
            halt
        """
        # registers
        registers = ("Z", "T")
        # expected messages
        messages = [
            # before "mov ax, 77"
            "Z=0,T=0",
            # before "mul ax, 900"
            "Z=0,T=0",
            # before "mul ax, 0"
            "Z=0,T=1",
            # before "halt"
            "Z=1,T=0",
        ]

        assert_registers(assembly, registers, messages)

    def test_imul__flags(self):
        """IMUL should set flags N, Z and V"""

        # instructions
        assembly = """
            mov ax, 80
            imul ax, -900
            imul ax, 0
            halt
        """
        # registers
        registers = ("N", "Z", "V")
        # expected messages
        messages = [
            # before "mov ax, 80"
            "N=0,Z=0,V=0",
            # before "imul ax, -900"
            "N=0,Z=0,V=0",
            # before "imul ax, 0"
            "N=1,Z=0,V=1",
            # before "halt"
            "N=0,Z=1,V=0",
        ]

        assert_registers(assembly, registers, messages)

    def test_div__reg_reg(self):
        """DIV should calculate quotient of two registers"""

        # instructions
        assembly = """
            mov ax, 7
            mov bx, 2
            div ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 7"
            "AX=0,BX=0",
            # before "mov bx, 2"
            "AX=7,BX=0",
            # before "div ax, bx"
            "AX=7,BX=2",
            # before "halt"
            "AX=3,BX=2",
        ]

        assert_registers(assembly, registers, messages)

    def test_div__flags(self):
        """DIV should set flag Z"""

        # instructions
        assembly = """
            mov ax, 3
            div ax, 3
            div ax, 4
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 3"
            "Z=0",
            # before "div ax, 3"
            "Z=0",
            # before "div ax, 4"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_mod__reg_reg(self):
        """MOD should calculate remainder of two registers"""

        # instructions
        assembly = """
            mov ax, 7
            mov bx, 2
            mod ax, bx
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 7"
            "AX=0,BX=0",
            # before "mov bx, 2"
            "AX=7,BX=0",
            # before "mod ax, bx"
            "AX=7,BX=2",
            # before "halt"
            "AX=1,BX=2",
        ]

        assert_registers(assembly, registers, messages)

    def test_mod__flags(self):
        """MOD should set flag Z"""

        # instructions
        assembly = """
            mov ax, 9
            mod ax, 3
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 9"
            "Z=0",
            # before "mod ax, 3"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_cmp(self):
        """CMP should compare two values and set flags N and Z"""

        # instructions
        assembly = """
            mov ax, 5
            cmp ax, 5
            cmp ax, 6
            cmp ax, 4
            halt
        """
        # registers
        registers = ("N", "Z")
        # expected messages
        messages = [
            # before "mov ax, 5"
            "N=0,Z=0",
            # before "cmp ax, 5"
            "N=0,Z=0",
            # before "cmp ax, 6"
            "N=0,Z=1",
            # before "cmp ax, 4"
            "N=1,Z=0",
            # before "halt"
            "N=0,Z=0",
        ]

        assert_registers(assembly, registers, messages)

    def test_icmp(self):
        """ICMP should signed compare two values and set flags N and Z"""

        # instructions
        assembly = """
            mov ax, -7
            icmp ax, -7
            icmp ax, 2
            icmp ax, -15
            halt
        """
        # registers
        registers = ("N", "Z")
        # expected messages
        messages = [
            # before "mov ax, -7"
            "N=0,Z=0",
            # before "cmp ax, -7"
            "N=0,Z=0",
            # before "cmp ax, 2"
            "N=0,Z=1",
            # before "cmp ax, -15"
            "N=1,Z=0",
            # before "halt"
            "N=0,Z=0",
        ]

        assert_registers(assembly, registers, messages)


class TestCPU__UC:
    """CPU (Control Unit)"""

    def test_mov__reg_reg(self):
        """MOV should load a register from another register"""

        # mov instructions
        assembly = """
            mov ax, 3
            mov bx, ax
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 3"
            "AX=0,BX=0",
            # before "mov bx, ax"
            "AX=3,BX=0",
            # before "halt"
            "AX=3,BX=3",
        ]

        assert_registers(assembly, registers, messages)

    def test_mov__high_low(self):
        """MOV should allow setting most and less significant register areas"""

        # mov instructions
        assembly = """
            mov al, 0x9A
            mov ah, 0x10
            mov ax, 0x9F8D
            halt
        """
        # registers
        registers = ("AX", "AH", "AL")
        # expected messages
        messages = [
            "AX=%d,AH=%d,AL=%d" % (0x0, 0x0, 0x0),  # "mov al, 0x9A"
            "AX=%d,AH=%d,AL=%d" % (0x009A, 0x00, 0x9A),  # "mov ah, 0x10"
            "AX=%d,AH=%d,AL=%d" % (0x109A, 0x10, 0x9A),  # "mov ax, 0x9F8D"
            "AX=%d,AH=%d,AL=%d" % (0x9F8D, 0x9F, 0x8D),
        ]  # "halt"

        assert_registers(assembly, registers, messages)

    def test_mov__reg_const(self):
        """MOV should load a register from a constant"""

        # mov instructions
        assembly = """
            mov ax, 9
            mov bx, 4
            halt
        """
        # registers
        registers = ("AX", "BX")
        # expected messages
        messages = [
            # before "mov ax, 9"
            "AX=0,BX=0",
            # before "mov bx, 4"
            "AX=9,BX=0",
            # before "halt"
            "AX=9,BX=4",
        ]

        assert_registers(assembly, registers, messages)

    def test_mov__reg_mem(self):
        """MOV should load a register from a memory position"""

        # mov instructions
        assembly = """
            mov ax, 7
            mov [128], ax
            mov bx, [128]
            halt
        """
        # registers
        registers = ("BX",)
        # expected messages
        messages = [
            # before "mov ax, 7"
            "BX=0",
            # before "mov [128], ax"
            "BX=0",
            # before "mov bx, [128]"
            "BX=0",
            # before "halt"
            "BX=7",
        ]

        assert_registers(assembly, registers, messages)

    def test_mov__mem_reg(self):
        """MOV should load a memory position from a register"""

        # mov instructions
        assembly = """
            mov ax, 5
            mov [128], ax
            halt
        """
        # memory addresses
        addresses = (128,)
        # expected messages
        messages = [
            # before "mov ax, 5"
            "[128]=0",
            # before "mov [128], ax"
            "[128]=0",
            # before "halt"
            "[128]=5",
        ]

        assert_memory(assembly, addresses, messages)

    def test_jz_je(self):
        """JZ/JE should set PC register when Z=1"""

        # instructions
        assembly = """
            mov ax, 1
            detour:
            dec ax
            jz detour
            cmp ax, 65535
            je detour
            halt
        """
        # registers
        registers = ("PC",)
        # expected messages
        messages = [
            # before "mov ax, 1"
            "PC=0",
            # before "dec ax"
            "PC=2",
            # before "jz detour"
            "PC=3",
            # before "dec ax"
            "PC=2",
            # before "jz detour"
            "PC=3",
            # before "cmp ax, 65535"
            "PC=4",
            # before "je detour"
            "PC=6",
            # before "dec ax"
            "PC=2",
            # before "jz detour"
            "PC=3",
            # before "cmp ax, 65535"
            "PC=4",
            # before "je detour"
            "PC=6",
            # before "halt"
            "PC=7",
        ]

        assert_registers(assembly, registers, messages)


class TestCPU__SHIFT:
    """CPU (Shift Unit)"""

    def test_shl(self):
        """SHL should shift left a value"""

        # instructions
        assembly = """
            mov ax, 0b100
            shl ax, 2
            halt
        """
        # registers
        registers = ("AX",)
        # expected messages
        messages = [
            # before "mov ax, 0b100"
            "AX=0",
            # before "shr ax, bx"
            "AX=4",
            # before "halt"
            "AX=16",
        ]

        assert_registers(assembly, registers, messages)

    def test_shl__flags(self):
        """SHL should set flag Z"""

        # instructions
        assembly = """
            mov ax, 0x4000
            shl ax, 1
            shl ax, 1
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 0x4000"
            "Z=0",
            # before "shl ax, 1"
            "Z=0",
            # before "shl ax, 1"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)

    def test_shr(self):
        """SHR should shift right a value"""

        # instructions
        assembly = """
            mov ax, 0b1000
            shr ax, 2
            halt
        """
        # registers
        registers = ("AX",)
        # expected messages
        messages = [
            # before "mov ax, 0b100"
            "AX=0",
            # before "shr ax, bx"
            "AX=8",
            # before "halt"
            "AX=2",
        ]

        assert_registers(assembly, registers, messages)

    def test_shr__flags(self):
        """SHR should set flag Z"""

        # instructions
        assembly = """
            mov ax, 0x0001
            shr ax, 1
            halt
        """
        # registers
        registers = "Z"
        # expected messages
        messages = [
            # before "mov ax, 0x0001"
            "Z=0",
            # before "shr ax, 1"
            "Z=0",
            # before "halt"
            "Z=1",
        ]

        assert_registers(assembly, registers, messages)
