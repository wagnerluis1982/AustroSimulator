# Copyright (C) 2013  Wagner Macedo <wagnerluis1982@gmail.com>
#
# This file is part of Austro Simulator.
#
# Austro Simulator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Austro Simulator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Austro Simulator.  If not, see <http://www.gnu.org/licenses/>.

"""CPU simulator functionality"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from ctypes import c_int8, c_int16
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Iterator, Sequence, cast, override

from austro.asm.assembler import OPCODES, REGISTERS
from austro.asm.memword import DWord, Word
from austro.shared import AustroException
from austro.simulator.register import Reg16, RegH, RegL, RegX


if TYPE_CHECKING:
    from austro.simulator.register import BaseReg


class StepListener(metaclass=ABCMeta):
    @abstractmethod
    def on_fetch(self, registers: Registers, memory: Memory) -> None: ...


@dataclass(init=False)
class Decode:
    unit: int
    operation: int
    op1: None | int = None
    op2: None | int = None
    store: None | bool | int = None


class Stage(Enum):
    INITIAL = 0
    STOPPED = 1
    FETCH = 2
    DECODE = 3
    EXECUTE = 4
    STORE = 5
    HALTED = 6


class CPU:
    ADDRESS_SPACE = 256

    # Execution units
    ALU = 0
    UC = 1
    SHIFT = 2

    # Special UC actions
    UC_LOAD = 128

    def __init__(self, *listeners: StepListener) -> None:
        self.listeners: list[StepListener] = []
        if listeners is not None:
            self.listeners.extend(listeners)

        self.memory = Memory(CPU.ADDRESS_SPACE)
        self.registers = Registers()
        self.stage = Stage.INITIAL

    def set_memory_block(self, words: Sequence[Word], start=0) -> bool:
        assert isinstance(words, (list, tuple))
        if start + len(words) > self.memory.size:
            raise CPUException(
                "Error: tried to set memory to outside address space: {0} > {1}".format(
                    start + len(words), self.memory.size
                )
            )

        for word in words:
            self.memory.set_word(start, word)
            start += 1

        return True

    def start(self) -> bool:
        while self.stage not in (Stage.HALTED, Stage.STOPPED):
            next(self)

        if self.stage == Stage.STOPPED:
            return False

        return True

    def __next__(self) -> bool:
        try:
            return self._do_next()
        except CPUException:
            self.stop()
            raise

    def _do_next(self) -> bool:
        registers = self.registers
        memory = self.memory

        # See if stop method was called
        if self.stage == Stage.STOPPED:
            return False

        # Initial state, for starting, PC=0.
        elif self.stage == Stage.INITIAL:
            registers["PC"] = 0
            return self.fetch()

        # Decode stage
        elif self.stage == Stage.DECODE:
            decode = self.decode(registers.get_word("RI"))
            op1_val = None if decode.op1 is None else registers[decode.op1]
            op2_val = None if decode.op2 is None else registers[decode.op2]
            # Next state
            self.stage = Stage.EXECUTE

        # Execute stage
        if self.stage == Stage.EXECUTE:
            # Call ALU (Arithmetic and Logic Unit)
            if decode.unit == CPU.ALU:
                result = self.alu(decode.operation, cast(int, op1_val), cast(int, op2_val))
                # Invalid instructions behave as NOP
                if result is None:
                    decode.store = None
            # Call UC (Control Unit)
            elif decode.unit == CPU.UC:
                self.uc(decode.operation, decode.op1, decode.op2)
                if self.stage == Stage.HALTED:  # halt found
                    return True
                if self.stage == Stage.FETCH:  # a jump found
                    return self.fetch()
            # Call SU (Shift Unit)
            elif decode.unit == CPU.SHIFT:
                result = self.shift(decode.operation, op1_val, op2_val)

            # Next state: store or fetch
            if self.stage != Stage.FETCH:
                if type(decode.store) is bool and decode.store or decode.store is not None:
                    self.stage = Stage.STORE
                else:
                    self.stage = Stage.FETCH
                    registers["PC"] += 1
                    return self.fetch()

        # Store stage
        if self.stage == Stage.STORE:
            if decode.unit != CPU.UC:
                self.uc(CPU.UC_LOAD, decode.op1, result)
            if type(decode.store) is int:
                assert isinstance(decode.op1, int)
                memory[decode.store] = registers[decode.op1]

        # Fetch stage
        self.stage = Stage.FETCH
        registers["PC"] += 1
        return self.fetch()

    def fetch(self) -> bool:
        registers = self.registers

        # PC can't be greater than address space
        if registers["PC"] >= CPU.ADDRESS_SPACE:
            raise CPUException("PC register greater than address space")

        registers["MAR"] = registers["PC"]
        registers.set_word("MBR", self.memory.get_word(registers["MAR"]))
        registers.set_word("RI", registers.get_word("MBR"))

        # Emit event
        for listener in self.listeners:
            listener.on_fetch(self.registers, self.memory)

        self.stage = Stage.DECODE
        return True

    def stop(self) -> None:
        self.stage = Stage.STOPPED

    def reset(self) -> None:
        self.memory.clear()
        self.registers.clear()
        self.stage = Stage.INITIAL

    #
    ## Implementation of CPU execution units
    #

    # Control Unit
    def uc(self, operation: int, op1: None | int, op2: None | int) -> None:
        registers = self.registers

        # Special actions
        if operation >= 128:
            if operation == CPU.UC_LOAD:
                assert isinstance(op1, int)
                assert isinstance(op2, int)
                registers[op1] = op2
            return

        _ = self._opcodes
        opcode = operation

        if opcode in _("HALT"):
            self.stage = Stage.HALTED
        elif opcode in _("MOV"):
            assert isinstance(op1, int)
            assert isinstance(op2, int)
            registers[op1] = registers[op2]
        # Jump instructions
        elif opcode in _("JZ", "JE"):
            assert isinstance(op1, int)
            if registers["Z"] == 1:
                self._jump_to(registers[op1])
        elif opcode in _("JNZ", "JNE"):
            assert isinstance(op1, int)
            if registers["Z"] == 0:
                self._jump_to(registers[op1])
        elif opcode in _("JN", "JLT"):
            assert isinstance(op1, int)
            if registers["N"] == 1:
                self._jump_to(registers[op1])
        elif opcode in _("JP", "JGT"):
            assert isinstance(op1, int)
            if registers["Z"] == 0 and registers["N"] == 0:
                self._jump_to(registers[op1])
        elif opcode in _("JGE"):
            assert isinstance(op1, int)
            if registers["N"] == 0:
                self._jump_to(registers[op1])
        elif opcode in _("JLE"):
            assert isinstance(op1, int)
            if registers["Z"] == 1 or registers["N"] == 1:
                self._jump_to(registers[op1])
        elif opcode in _("JV"):
            assert isinstance(op1, int)
            if registers["V"] == 1:
                self._jump_to(registers[op1])
        elif opcode in _("JT"):
            assert isinstance(op1, int)
            if registers["T"] == 1:
                self._jump_to(registers[op1])
        elif opcode in _("JMP"):
            assert isinstance(op1, int)
            self._jump_to(registers[op1])
        # opcode == 'NOP' or invalid
        else:
            registers["PC"] += 1
            self.stage = Stage.FETCH

    # Arithmetic and Logic Unit
    def alu(self, operation: int, in1: int, in2: int) -> int | None:
        _ = self._opcodes
        registers = self.registers

        opcode = operation >> 2
        bits = 8 if operation & 0b10 else 16
        result = None

        # Treat inputs as signed if desired
        signed = operation & 0b1
        if signed:
            # 8-bit inputs
            if bits == 8:
                in1 = c_int8(in1).value
                in2 = c_int8(in2).value
            # 16-bit inputs
            else:
                in1 = c_int16(in1).value
                in2 = c_int16(in2).value

        # Bitwise OR
        if opcode in _("OR"):
            result = in1 | in2
        # Bitwise AND
        elif opcode in _("AND"):
            result = in1 & in2
        # Bitwise NOT
        elif opcode in _("NOT"):
            result = ~in1
        # Increment
        elif opcode in _("INC"):
            result = in1 + 1
            # Overflow
            registers["V"] = int(result >> bits != 0)
        # Decrement
        elif opcode in _("DEC"):
            result = in1 - 1
            # Overflow
            registers["V"] = int(result >> bits != 0)
        # Bitwise XOR
        elif opcode in _("XOR"):
            result = in1 ^ in2
        # Addition
        elif opcode in _("ADD"):
            result = in1 + in2
            # Overflow
            registers["V"] = int(result >> bits != 0)
        # Subtraction
        elif opcode in _("SUB"):
            result = in1 - in2
            # Overflow
            registers["V"] = int(result >> bits != 0)
        # Multiplication
        elif opcode in _("MUL"):
            result = in1 * in2
            # Transport handling (excess)
            if not signed:
                transport = result >> bits
                registers["T"] = int(transport > 0)
                if registers["T"] == 1:
                    registers["SP"] = transport
            # Negative and Overflow
            else:
                registers["N"] = int(result < 0)
                registers["V"] = int(result >> bits != 0)
        # Division
        elif opcode in _("DIV"):
            result = in1 // in2
            if signed:
                registers["N"] = int(result < 0)
        # Remainder
        elif opcode in _("MOD"):
            result = in1 % in2
            if signed:
                registers["N"] = int(result < 0)
        # Comparison
        elif opcode in _("CMP"):
            tmp = in1 - in2
            registers["N"] = int(tmp < 0)
            registers["Z"] = int(tmp == 0)

        # Zero
        if result is not None:
            mask = 0xFF if bits == 8 else 0xFFFF
            registers["Z"] = result & mask == 0 and 1 or 0

        return result

    # Shift Unit
    def shift(self, operation, op, n):
        _ = self._opcodes
        registers = self.registers
        opcode = operation >> 1
        is_8bits = operation & 0b1

        if opcode in _("SHR"):
            result = op >> n
        elif opcode in _("SHL"):
            result = op << n

        # Zero
        mask = 0xFF if is_8bits else 0xFFFF
        registers["Z"] = result & mask == 0 and 1 or 0

        return result

    #
    ## Decoder
    #

    def decode(self, instr_word: Word) -> Decode:
        dcd = Decode()
        instr_word.is_instruction = True

        # Aliases
        registers = self.registers
        memory = self.memory

        # Argument type
        argtype = self._arg_type(instr_word.opcode)

        flags = instr_word.flags
        operand = instr_word.operand

        if argtype in ("DST_ORI", "OP1_OP2"):
            dcd.store = True  # for store stage
            order = flags & 0b011
            # Reg, Reg
            if order == 0:
                dcd.op1 = operand >> 4
                dcd.op2 = operand & 0b1111
            # Situations that need next word
            else:
                registers["PC"] += 1  # increment PC
                registers["MAR"] = registers["PC"]
                registers["MBR"] = memory[registers["MAR"]]
                # Reg, Mem
                if order == 1:
                    dcd.op1 = operand >> 4
                    # Getting memory reference
                    registers["PC"] = registers["MBR"]
                    registers["TMP"] = memory[registers["PC"]]
                    registers["PC"] = registers["MAR"]
                    dcd.op2 = Registers.INDEX["TMP"]
                # Reg, Const
                elif order == 2:
                    dcd.op1 = operand >> 4
                    dcd.op2 = Registers.INDEX["MBR"]
                # Mem, Reg
                else:
                    dcd.op2 = operand >> 4
                    # Fetching memory reference
                    registers["PC"] = registers["MBR"]
                    registers["TMP"] = memory[registers["PC"]]
                    registers["PC"] = registers["MAR"]
                    dcd.op1 = Registers.INDEX["TMP"]
                    # Setting memory address for store stage
                    dcd.store = registers["MBR"]

        elif argtype == "OP_QNT":
            order = flags & 0b001
            # Operand => Reg
            if order == 0:
                dcd.op1 = operand >> 4
                dcd.store = True
            # Operand => Mem
            else:
                # Fetching memory reference
                registers["MAR"] = registers["PC"]
                registers["PC"] = operand
                registers["TMP"] = memory[registers["PC"]]
                registers["PC"] = registers["MAR"]
                dcd.op1 = Registers.INDEX["TMP"]
                # Setting memory address for store stage
                dcd.store = operand
            # Quantity (next word)
            registers["PC"] += 1  # increment PC
            registers["MAR"] = registers["PC"]
            registers["MBR"] = memory[registers["MAR"]]
            dcd.op2 = Registers.INDEX["MBR"]

        elif argtype == "JUMP":
            order = flags & 0b011
            # End => Register
            if order == 0:
                dcd.op1 = operand >> 4
            # End => Memory
            elif order == 1:
                # Fetching memory reference
                registers["MAR"] = registers["PC"]
                registers["PC"] = operand
                registers["TMP"] = memory[registers["PC"]]
                registers["PC"] = registers["MAR"]
                dcd.op1 = Registers.INDEX["TMP"]
            # End => Constant
            elif order == 2:
                registers["TMP"] = operand
                dcd.op1 = Registers.INDEX["TMP"]

        elif argtype == "OP":
            order = flags & 0b001
            # Operand => Reg
            if order == 0:
                dcd.op1 = operand >> 4
                dcd.store = True
            # Operand => Mem
            else:
                # Fetching memory reference
                registers["MAR"] = registers["PC"]
                registers["PC"] = operand
                registers["TMP"] = memory[registers["PC"]]
                registers["PC"] = registers["MAR"]
                dcd.op1 = Registers.INDEX["TMP"]
                # Setting memory address for store stage
                dcd.store = operand

        # Setting execution unit
        _ = self._opcodes
        if instr_word.opcode in _("SHR", "SHL"):
            dcd.unit = CPU.SHIFT
            assert dcd.op1 is not None
            is_8bits = dcd.op1 < 8  # destination is an 8-bit register?
            dcd.operation = (instr_word.opcode << 1) | is_8bits
        elif instr_word.opcode >= 16:
            dcd.unit = CPU.ALU
            # ALU see if last bit is 1, mean a signed operation
            signed = (flags & 0b100) >> 2
            assert dcd.op1 is not None
            is_8bits = dcd.op1 < 8  # destination is an 8-bit register?
            alu_flags = is_8bits << 1 | signed
            dcd.operation = (instr_word.opcode << 2) | alu_flags
        else:
            dcd.unit = CPU.UC
            dcd.operation = instr_word.opcode
            # Only memory words are passed to store on UC instructions
            if dcd.store is True:
                dcd.store = None

        return dcd

    # Helper to jump instructions
    def _jump_to(self, newpc):
        self.registers["PC"] = newpc
        self.stage = Stage.FETCH

    def _opcodes(self, *opnames):
        for name in opnames:
            yield OPCODES[name]

    def _arg_type(self, opcode):
        _ = self._opcodes

        if opcode in _("MOV", "ADD", "SUB", "MUL", "OR", "AND", "XOR", "DIV", "MOD"):
            return "DST_ORI"

        if opcode in _("CMP"):
            return "OP1_OP2"

        if opcode in _("SHR", "SHL"):
            return "OP_QNT"

        if opcode in _(
            "JZ", "JE", "JNZ", "JNE", "JN", "JLT", "JP", "JGT", "JGE", "JLE", "JV", "JT", "JMP"
        ):
            return "JUMP"

        if opcode in _("INC", "DEC", "NOT"):
            return "OP"

        return "NOARG"


class Registers:
    """Container to store the CPU registers"""

    # Map of register names as keys and it number identifiers as values
    INDEX: dict[str, int] = {
        **REGISTERS,
        **{
            # Specific registers
            "PC": 16,
            "RI": 17,
            "MAR": 18,
            "MBR": 19,
            # State registers
            "N": 20,
            "Z": 21,
            "V": 22,
            "T": 23,
            # Internal (not visible)
            "TMP": 90,
        },
    }

    def __init__(self) -> None:
        self._regwords: dict[int, RegisterWord] = {}

        # Internal function to set register objects
        def init_register(name: str, register: BaseReg):
            self._regwords[Registers.INDEX[name]] = RegisterWord(register)

        #
        ## Generic registers
        #
        for name in "AX", "BX", "CX", "DX":
            init_register(name, RegX())
        # Index for generic registers
        index_regx = {k: self._regwords[Registers.INDEX[f"{k}X"]]._reg for k in "ABCD"}
        for k, regx in index_regx.items():
            assert isinstance(regx, RegX)
            # 8-bit most significant registers: AH, BH, CH, DH
            init_register(f"{k}H", RegH(regx))
            # 8-bit less significant registers: AL, BL, CL, DL
            init_register(f"{k}L", RegL(regx))
        # 16-bit only registers
        for name in "SP", "BP", "SI", "DI":
            init_register(name, Reg16())

        #
        ## Specific registers
        #
        for name in "PC", "MAR":
            init_register(name, Reg16())

        for name in "RI", "MBR":
            init_register(name, Reg16())

        #
        ## State registers
        #
        for name in "N", "Z", "V", "T":
            init_register(name, Reg16())

        #
        ## Internal
        #
        init_register("TMP", Reg16())

    def clear(self):
        for w in self._regwords.values():
            w._reg.value = 0

    def get_reg(self, key: int | str) -> BaseReg:
        assert isinstance(key, (int, str))

        if isinstance(key, str):
            key = Registers.INDEX[key]

        return self._regwords[key]._reg

    def set_word(self, key: int | str, word: Word) -> None:
        """Convenient way to store a word value in a register."""
        assert isinstance(key, (int, str))
        assert isinstance(word, Word)

        if isinstance(key, str):
            key = Registers.INDEX[key]

        regword = self._regwords[key]
        assert regword.bits >= word.bits, (
            f"Cannot store a {word.bits}-bit word into a {regword.bits}"
        )

        # copy value and metadata
        regword._reg.value = word.value
        regword.is_instruction = word.is_instruction
        regword.lineno = word.lineno

    def get_word(self, key: int | str) -> Word:
        assert isinstance(key, (int, str))

        if isinstance(key, str):
            key = Registers.INDEX[key]

        return self._regwords[key]

    def __setitem__(self, key: int | str, value: int):
        assert isinstance(key, (int, str))
        assert isinstance(value, int)

        if isinstance(key, str):
            key = Registers.INDEX[key]

        self._regwords[key]._reg.value = value

    def __getitem__(self, key: int | str) -> int:
        assert isinstance(key, (int, str))

        if isinstance(key, str):
            key = Registers.INDEX[key]

        return self._regwords[key]._reg.value

    def __iter__(self) -> Iterator[tuple[int, BaseReg]]:
        for id, word in self._regwords.items():
            yield id, word._reg


class Memory:
    def __init__(self, size: int) -> None:
        self._size = size
        self._space: list[Word] = []
        for i in range(size):
            self._space.append(DWord())

    def set_word(self, address: int, word: Word) -> None:
        assert isinstance(address, int)
        assert isinstance(word, Word)

        if not (0 <= address < self._size):
            raise CPUException("Address out of memory range")

        space_word = self._space[address]
        space_word.is_instruction = word.is_instruction
        space_word.value = word.value
        if word.is_instruction:
            space_word.lineno = word.lineno

    def get_word(self, address: int) -> Word:
        assert isinstance(address, int)

        if not (0 <= address < self._size):
            raise CPUException("Address out of memory range")

        return self._space[address]

    def __setitem__(self, address: int, data: int) -> None:
        assert isinstance(address, int)
        assert isinstance(data, int)

        if not (0 <= address < self._size):
            raise CPUException("Address out of memory range")

        self._space[address].value = data

    def __getitem__(self, address: int) -> int:
        assert isinstance(address, int)

        if not (0 <= address < self._size):
            raise CPUException("Address out of memory range")

        return self._space[address].value

    def __iter__(self) -> Iterator[tuple[int, Word]]:
        for w in enumerate(self._space):
            yield w

    def clear(self):
        for word in self._space:
            word.value = 0

    @property
    def size(self) -> int:
        return self._size


class RegisterWord(Word):
    bits = 16

    def __init__(self, register: BaseReg):
        self._reg = register

    @Word.value.getter
    @override
    def value(self) -> int:
        return self._reg.value

    @value.setter  # type: ignore[no-redef]
    @override
    def value(self, val: int) -> None:
        raise CPUException("RegisterWord is read-only view of the register value")


class CPUException(AustroException):
    pass
