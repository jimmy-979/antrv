import re
from typing import ClassVar

from capstone import CS_ARCH_RISCV, CS_MODE_RISCV32, Cs


class RiscVDisassembler:
    ABI_TO_X: ClassVar[dict[str, str]] = {
        "zero": "x0",
        "ra": "x1",
        "sp": "x2",
        "gp": "x3",
        "tp": "x4",
        **{f"t{i}": f"x{5 + i}" for i in range(3)},
        "s0": "x8",
        "fp": "x8",
        "s1": "x9",
        **{f"a{i}": f"x{10 + i}" for i in range(8)},
        "s2": "x18",
        "s3": "x19",
        "s4": "x20",
        "s5": "x21",
        "s6": "x22",
        "s7": "x23",
        "s8": "x24",
        "s9": "x25",
        "s10": "x26",
        "s11": "x27",
        **{f"t{i}": f"x{25 + i}" for i in range(3, 7)},
    }

    def __init__(self):
        self._disassembler = Cs(CS_ARCH_RISCV, CS_MODE_RISCV32)

    def disassemble(self, instruction: int, pc: int = 0) -> str:
        """Disassemble a single 32-bit RISC-V instruction."""

        if not 0 <= instruction <= 0xFFFFFFFF:
            raise ValueError(
                f"Instruction must be a 32-bit unsigned integer: {instruction}"
            )

        instruction_bytes = instruction.to_bytes(4, byteorder="little")

        decoded = next(
            self._disassembler.disasm(instruction_bytes, pc, count=1),
            None,
        )

        if decoded is None:
            return f".word 0x{instruction:08x}"

        op_str = decoded.op_str

        for abi_name in sorted(self.ABI_TO_X, key=len, reverse=True):
            op_str = re.sub(
                rf"\b{re.escape(abi_name)}\b",
                self.ABI_TO_X[abi_name],
                op_str,
            )

        return f"{decoded.mnemonic} {op_str}".rstrip()
