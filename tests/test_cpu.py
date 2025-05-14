from __future__ import annotations

import re

from typing import TYPE_CHECKING, Sequence, override

import pytest

from austro.asm.assembler import REGISTERS, assemble
from austro.asm.memword import DWord
from austro.simulator.cpu import CPU, CPUException, Registers, RegisterWord, Stage, StepListener
from austro.simulator.register import Reg16


if TYPE_CHECKING:
    from austro.simulator.cpu import Memory


class ShowCpuState(StepListener):
    def __init__(self, *identifiers: int | str) -> None:
        self.history: list[str] = []
        self.fmt = ",".join(
            [f"{'@%d' % id if isinstance(id, int) else id}=%d" for id in identifiers]
        )

        self.indexes: list[int | str] = []
        for id in identifiers:
            self.indexes.append(id)

    @override
    def on_fetch(self, registers: Registers, memory: Memory) -> None:
        args = [registers[idx] if isinstance(idx, str) else memory[idx] for idx in self.indexes]
        self.history.append(self.fmt % tuple(args))


@pytest.fixture
def cpu():
    return CPU()


def assert_cpu_history(
    assembly: str, identifiers: Sequence[int | str], history: Sequence[str]
) -> None:
    # instructions
    asmd = assemble(assembly)

    listener = ShowCpuState(*identifiers)
    cpu = CPU(listener)
    cpu.set_memory_block(asmd["words"])

    # Test run
    assert cpu.start() is True

    # Test captured history
    assert len(listener.history) == len(history)

    history = [re.sub(r"\[(\d+)\]=(.+)", r"@\1=\2", h.replace(" ", "")) for h in history]
    for i in range(len(history)):
        pattern = history[i]
        actual = listener.history[i]
        assert re.match(pattern, actual) is not None, (
            f"[{i}] '{actual}' does not match '{pattern}'"
        )


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
        # expected history
        history = [
            "AX=0, BX=0 ",  # mov ax, 0b1001
            "AX=9, BX=0 ",  # mov bx, 0b1100
            "AX=9, BX=12",  # or ax, bx
            "AX=13,BX=12",  # halt           | AX = 0b1001 & 0b1100 => 0b1101 => 13
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 0
            "Z=0",  # or ax, 1
            "Z=0",  # mov ax, 0
            "Z=0",  # or ax, 0
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0, BX=0",  # mov ax, 0b1100
            "AX=12,BX=0",  # mov bx, 0b0110
            "AX=12,BX=6",  # and ax, bx
            "AX=4, BX=6",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 1
            "Z=0",  # and ax, 0
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=%d" % 0x0000,  # mov ax, 0xabcd
            "AX=%d" % 0xABCD,  # not ax
            "AX=%d" % 0x5432,  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_not__memory(self):
        """NOT should invert all bits of a value"""

        # instructions
        assembly = """
            mov ax, 0xabcd
            mov [128], ax
            not [128]
            halt
        """
        # memory addresses
        addresses = (128,)
        # expected history
        history = [
            "[128]=%d" % 0x0000,  # mov ax, 0xabcd
            "[128]=%d" % 0x0000,  # mov [128], ax
            "[128]=%d" % 0xABCD,  # not [128]
            "[128]=%d" % 0x5432,  # halt
        ]

        assert_cpu_history(assembly, addresses, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 0xffff
            "Z=0",  # not ax
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0, BX=0 ",  # mov ax, 0b1100
            "AX=12,BX=0 ",  # mov bx, 0b1010
            "AX=12,BX=10",  # xor ax, bx
            "AX=6, BX=10",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 1
            "Z=0",  # xor ax, 1
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0,  BX=0  ",  # mov ax, 193
            "AX=193,BX=0  ",  # mov bx, 297
            "AX=193,BX=297",  # add ax, bx
            "AX=490,BX=297",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0,V=0",  # mov ax, 65534
            "Z=0,V=0",  # mov bx, 65535
            "Z=0,V=0",  # add ax, 1
            "Z=0,V=0",  # add ax, 1
            "Z=1,V=1",  # add bx, 2
            "Z=0,V=1",  # mov cl, 255
            "Z=0,V=1",  # add cl, 1
            "Z=1,V=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0, BX=0 ",  # mov ax, 19
            "AX=19,BX=0 ",  # mov bx, 10
            "AX=19,BX=10",  # sub ax, bx
            "AX=9, BX=10",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0,V=0",  # mov ax, 1
            "Z=0,V=0",  # mov bx, 1
            "Z=0,V=0",  # sub ax, 2
            "Z=0,V=1",  # sub bx, 1
            "Z=1,V=0",  # sub bx, 1
            "Z=0,V=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0 ",  # mov ax, 9
            "AX=9 ",  # inc ax
            "AX=10",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0,V=0",  # mov ax, 0xfffe
            "Z=0,V=0",  # inc ax
            "Z=0,V=0",  # inc ax
            "Z=1,V=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0  ",  # mov ax, 100
            "AX=100",  # dec ax
            "AX=99 ",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0,V=0",  # mov ax, 1
            "Z=0,V=0",  # dec ax
            "Z=1,V=0",  # dec ax
            "Z=0,V=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0, BX=0",  # mov ax, 12
            "AX=12,BX=0",  # mov bx, 5
            "AX=12,BX=5",  # mul ax, bx
            "AX=60,BX=5",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0,    SP=0",  # mov ax, 500
            "AX=500,  SP=0",  # mov sp, 8
            "AX=500,  SP=8",  # mul ax, 1
            "AX=500,  SP=8",  # mul ax, 850
            "AX=31784,SP=6",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0,T=0",  # mov ax, 77
            "Z=0,T=0",  # mul ax, 900
            "Z=0,T=1",  # mul ax, 0
            "Z=1,T=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "N=0,Z=0,V=0",  # mov ax, 80
            "N=0,Z=0,V=0",  # imul ax, -900
            "N=1,Z=0,V=1",  # imul ax, 0
            "N=0,Z=1,V=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_imul_8bits(self):
        """IMUL should set flags N, Z and V (8 bits registers)"""

        # instructions
        assembly = """
            mov ah, 80
            imul ah, -90
            imul ah, 0
            halt
        """
        # registers
        registers = ("N", "Z", "V")
        # expected history
        history = [
            "N=0,Z=0,V=0",  # mov ah, 80
            "N=0,Z=0,V=0",  # imul ah, -90
            "N=1,Z=0,V=1",  # imul ah, 0
            "N=0,Z=1,V=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0,BX=0",  # mov ax, 7
            "AX=7,BX=0",  # mov bx, 2
            "AX=7,BX=2",  # div ax, bx
            "AX=3,BX=2",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 3
            "Z=0",  # div ax, 3
            "Z=0",  # div ax, 4
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_idiv__flags(self):
        """IDIV should set flags N and Z"""

        # instructions
        assembly = """
            mov ax, 1
            idiv ax, -25
            mov bx, 0
            idiv bx, ax
            halt
        """
        # registers
        registers = ("N", "Z")
        # expected history
        history = [
            "N=0,Z=0",  # mov ax, 25
            "N=0,Z=0",  # idiv ax, -25
            "N=1,Z=0",  # mov bx, 0
            "N=1,Z=0",  # idiv bx, ax
            "N=0,Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0,BX=0",  # mov ax, 7
            "AX=7,BX=0",  # mov bx, 2
            "AX=7,BX=2",  # mod ax, bx
            "AX=1,BX=2",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 9
            "Z=0",  # mod ax, 3
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_imod__flags(self):
        """IMOD should set flags N and Z"""

        # instructions
        assembly = """
            mov ax, 1
            imod ax, -25
            mov bx, 0
            imod bx, ax
            halt
        """
        # registers
        registers = ("N", "Z")
        # expected history
        history = [
            "N=0,Z=0",  # mov ax, 25
            "N=0,Z=0",  # imod ax, -25
            "N=1,Z=0",  # mov bx, 0
            "N=1,Z=0",  # imod bx, ax
            "N=0,Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "N=0,Z=0",  # mov ax, 5
            "N=0,Z=0",  # cmp ax, 5
            "N=0,Z=1",  # cmp ax, 6
            "N=1,Z=0",  # cmp ax, 4
            "N=0,Z=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "N=0,Z=0",  # mov ax, -7
            "N=0,Z=0",  # cmp ax, -7
            "N=0,Z=1",  # cmp ax, 2
            "N=1,Z=0",  # cmp ax, -15
            "N=0,Z=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)


class TestCPU__UC:
    """CPU (Control Unit)"""

    def test_nop(self):
        """NOP do nothing"""

        # instructions
        assembly = """
            nop
            halt
        """
        # registers
        registers = ("PC", "N", "Z", "V", "T")
        # expected history
        history = [
            "PC=0, N=0,Z=0,V=0,T=0",  # nop
            "PC=1, N=0,Z=0,V=0,T=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0,BX=0",  # mov ax, 3
            "AX=3,BX=0",  # mov bx, ax
            "AX=3,BX=3",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=%d,AH=%d,AL=%d" % (0x0000, 0x00, 0x00),  # mov al, 0x9A
            "AX=%d,AH=%d,AL=%d" % (0x009A, 0x00, 0x9A),  # mov ah, 0x10
            "AX=%d,AH=%d,AL=%d" % (0x109A, 0x10, 0x9A),  # mov ax, 0x9F8D
            "AX=%d,AH=%d,AL=%d" % (0x9F8D, 0x9F, 0x8D),  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0,BX=0",  # mov ax, 9
            "AX=9,BX=0",  # mov bx, 4
            "AX=9,BX=4",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "BX=0",  # mov ax, 7
            "BX=0",  # mov [128], ax
            "BX=0",  # mov bx, [128]
            "BX=7",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "[128]=0",  # mov ax, 5
            "[128]=0",  # mov [128], ax
            "[128]=5",  # halt
        ]

        assert_cpu_history(assembly, addresses, history)

    def test_jmp__label(self):
        """JMP should jump unconditionally"""

        # instructions
        assembly = """
            jmp detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC",)
        # expected history
        history = [
            "PC=0",  # jmp detour
            "PC=2",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jmp__register(self):
        """JMP should jump using the address from a register value"""

        # instructions
        assembly = """
            mov ax, 4
            jmp ax
            nop
            halt
        """
        # registers
        registers = ("PC",)
        # expected history
        history = [
            "PC=0",  # mov ax, 4
            "PC=2",  # jmp ax
            "PC=4",  # halt      | skip nop
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jmp__memory(self):
        """JMP should jump using the address from a memory value"""

        # instructions
        assembly = """
            mov ax, 6
            mov [128], ax
            jmp [128]
            nop
            halt
        """
        # registers
        registers = ("PC",)
        # expected history
        history = [
            "PC=0",  # mov ax, 4
            "PC=2",  # mov [128], ax
            "PC=4",  # jmp [128]
            "PC=6",  # halt         | skip nop
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jz(self):
        """JZ should set PC register when Z=1 (jump if operation resulted in zero)"""

        # instructions
        assembly = """
            mov ax, 1
            dec ax
            jz detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "Z")
        # expected history
        history = [
            "PC=0, Z=0",  # mov ax, 1
            "PC=2, Z=0",  # dec ax
            "PC=3, Z=1",  # jz detour
            "PC=5, Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jnz(self):
        """JNZ should set PC register when Z=0 (jump if operation resulted in non zero)"""

        # instructions
        assembly = """
            mov ax, 1
            jnz detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "Z")
        # expected history
        history = [
            "PC=0, Z=0",  # mov ax, 1
            "PC=2, Z=0",  # jnz detour
            "PC=4, Z=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_je(self):
        """JE should set PC register when Z=1 (jump if Op1 == Op2 after CMP)"""

        # instructions
        assembly = """
            mov ax, 1
            cmp ax, 1
            je detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "Z")
        # expected history
        history = [
            "PC=0, Z=0",  # mov ax, 1
            "PC=2, Z=0",  # cmp ax, 1
            "PC=4, Z=1",  # je detour
            "PC=6, Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jne(self):
        """JNE should set PC register when Z=0 (jump if Op1 != Op2 after CMP)"""

        # instructions
        assembly = """
            mov ax, 1
            cmp ax, 0
            jne detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "Z")
        # expected history
        history = [
            "PC=0, Z=0",  # mov ax, 1
            "PC=2, Z=0",  # cmp ax, 0
            "PC=4, Z=0",  # jne detour
            "PC=6, Z=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jn(self):
        """JN should set PC register when N=1 (jump if operation resulted in negative)"""

        # instructions
        assembly = """
            mov ax, 1
            cmp ax, 2
            jn detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "N")
        # expected history
        history = [
            "PC=0, N=0",  # mov ax, 1
            "PC=2, N=0",  # cmp ax, 2
            "PC=4, N=1",  # jn detour
            "PC=6, N=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jp(self):
        """JP should set PC register when Z=0 and N=0 (jump if operation resulted in positive)"""

        # instructions
        assembly = """
            mov ax, 1
            cmp ax, 0
            jp detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "Z", "N")
        # expected history
        history = [
            "PC=0, Z=0, N=0",  # mov ax, 1
            "PC=2, Z=0, N=0",  # cmp ax, 0
            "PC=4, Z=0, N=0",  # jp detour
            "PC=6, Z=0, N=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jgt(self):
        """JGT should set PC register when Z=0 and N=0 (jump if Op1 > Op2 after CMP)"""

        # instructions
        assembly = """
            mov ax, 1
            cmp ax, 0
            jgt detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "Z", "N")
        # expected history
        history = [
            "PC=0, Z=0, N=0",  # mov ax, 1
            "PC=2, Z=0, N=0",  # cmp ax, 0
            "PC=4, Z=0, N=0",  # jgt detour
            "PC=6, Z=0, N=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jge(self):
        """JGE should set PC register when N=0 (jump if Op1 >= Op2 after CMP)"""

        # instructions
        assembly = """
            mov ax, 2
            mov bx, 0
            detour:
            inc bx
            cmp ax, bx
            jge detour
            halt
        """
        # registers
        registers = ("PC", "N")
        # expected history
        history = [
            "PC=0, N=0",  # mov ax, 2
            "PC=2, N=0",  # mov bx, 0
            "PC=4, N=0",  # inc bx      (1)
            "PC=5, N=0",  # cmp ax, bx  | ax=2 bx=1
            "PC=6, N=0",  # jge detour
            "PC=4, N=0",  # inc bx      (2)
            "PC=5, N=0",  # cmp ax, bx  | ax=2 bx=2
            "PC=6, N=0",  # jge detour
            "PC=4, N=0",  # inc bx      (3)
            "PC=5, N=0",  # cmp ax, bx  | ax=2 bx=2
            "PC=6, N=1",  # jge detour
            "PC=7, N=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jlt(self):
        """JLT should set PC register when N=1 (jump if Op1 < Op2 after CMP)"""

        # instructions
        assembly = """
            mov ax, 1
            cmp ax, 2
            jlt detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "N")
        # expected history
        history = [
            "PC=0, N=0",  # mov ax, 1
            "PC=2, N=0",  # cmp ax, 2
            "PC=4, N=1",  # jlt detour
            "PC=6, N=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jle(self):
        """JLE should set PC register when Z=1 or N=1 (jump if Op1 <= Op2 after CMP)"""

        # instructions
        assembly = """
            mov ax, 1
            mov bx, 3
            detour:
            dec bx
            cmp ax, bx
            jle detour
            halt
        """
        # registers
        registers = ("PC", "Z", "N")
        # expected history
        history = [
            "PC=0, Z=0, N=0",  # mov ax, 1
            "PC=2, Z=0, N=0",  # mov bx, 3
            "PC=4, Z=0, N=0",  # dec bx      (1)
            "PC=5, Z=0, N=0",  # cmp ax, bx | ax=1 bx=2
            "PC=6, Z=0, N=1",  # jle detour
            "PC=4, Z=0, N=1",  # dec bx      (2)
            "PC=5, Z=0, N=1",  # cmp ax, bx  | ax=1 bx=1
            "PC=6, Z=1, N=0",  # jle detour
            "PC=4, Z=1, N=0",  # dec bx      (3)
            "PC=5, Z=1, N=0",  # cmp ax, bx  | ax=1 bx=0
            "PC=6, Z=0, N=0",  # jle detour
            "PC=7, Z=0, N=0",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jv(self):
        """JV should set PC register when V=1 (jump if detected overflow)"""

        # instructions
        assembly = """
            mov ax, 0
            dec ax
            jv detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "V")
        # expected history
        history = [
            "PC=0, V=0",  # mov ax, 0
            "PC=2, V=0",  # dec ax
            "PC=3, V=1",  # jv detour
            "PC=5, V=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_jt(self):
        """JT should set PC register when T=1 (jump if detected transport)"""

        # instructions
        assembly = """
            mov ax, 0xfffe
            mul ax, 2
            jt detour
            nop
            detour:
            halt
        """
        # registers
        registers = ("PC", "T")
        # expected history
        history = [
            "PC=0, T=0",  # mov ax, 0xfffe
            "PC=2, T=0",  # mul ax, 2
            "PC=4, T=1",  # jt detour
            "PC=6, T=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)


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
        # expected history
        history = [
            "AX=0 ",  # mov ax, 0b100
            "AX=4 ",  # shl ax, 2
            "AX=16",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

    def test_shl__memory(self):
        """SHL should shift left a memory value"""

        # instructions
        assembly = """
            mov ax, 0b100
            mov [128], ax
            shl [128], 2
            halt
        """
        # memory addresses
        addresses = (128,)
        # expected history
        history = [
            "[128]=0 ",  # mov ax, 0b100
            "[128]=0 ",  # mov [128], ax
            "[128]=4 ",  # shr [128], 2
            "[128]=16",  # halt
        ]

        assert_cpu_history(assembly, addresses, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 0x4000
            "Z=0",  # shl ax, 1
            "Z=0",  # shl ax, 1
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "AX=0",  # mov ax, 0b100
            "AX=8",  # shr ax, 2
            "AX=2",  # halt
        ]

        assert_cpu_history(assembly, registers, history)

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
        # expected history
        history = [
            "Z=0",  # mov ax, 0x0001
            "Z=0",  # shr ax, 1
            "Z=1",  # halt
        ]

        assert_cpu_history(assembly, registers, history)


class TestRegisters:
    @pytest.fixture
    def registers(self):
        return Registers()

    def test_get_reg(self, registers: Registers):
        """Register can be retrieved by name or number"""
        reg_by_name = registers.get_reg("AX")
        reg_by_number = registers.get_reg(REGISTERS["AX"])
        assert reg_by_name is reg_by_number

        reg_by_name.value = 42
        assert reg_by_number.value == 42


class TestRegisterWord:
    def test_reg_word_wraps_register(self):
        reg = Reg16()
        reg.value = 7

        reg_word = RegisterWord(reg)
        assert reg_word.value == 7

        reg.value = 42
        assert reg_word.value == 42

    def test_reg_word_is_read_only(self):
        reg = Reg16()
        reg.value = 7

        reg_word = RegisterWord(reg)
        with pytest.raises(CPUException, match="RegisterWord is read-only"):
            reg_word.value = 42

        # value was not changed
        assert reg.value == 7
        assert reg_word.value == 7

    def test_reg_word_instruction_properties_can_be_read_normally(self):
        reg = Reg16()
        reg_word = RegisterWord(reg)
        reg_word.is_instruction = True

        # set to the maximum value
        reg.value = 0xFFFF
        assert reg_word.opcode == 31
        assert reg_word.flags == 7
        assert reg_word.operand == 0xFF
