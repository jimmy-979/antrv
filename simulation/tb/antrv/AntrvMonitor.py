import avl
import cocotb
from cocotb.triggers import FallingEdge, RisingEdge
from colorama import Fore, Style
from tb.components.InstructionTransaction import InstructionTransaction
from tb.utils.RiscVDisassembler import RiscVDisassembler


class AntrvMonitor(avl.Monitor):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.disassembler = RiscVDisassembler()
        self.cfg = None
        self.verbose = avl.Factory.get_variable(
            f"{self.get_full_name()}.verbose", False
        )

    async def run_phase(self):
        if self.cfg.interface.rstn.value == 1:
            await FallingEdge(self.cfg.interface.rstn)

        prev_pc = int(self.cfg.interface.pc.value)

        while True:
            pc = int(self.cfg.interface.pc.value)

            if pc == prev_pc:
                await RisingEdge(self.cfg.interface.clk)
                continue
            prev_pc = pc

            dump = await self.monitor_instruction()

            instruction = dump["instruction"]
            register_writes = dump["register_writes"]
            memory_writes = dump["memory_writes"]

            # Print disassembly
            assembly = self.disassembler.disassemble(instruction, pc)
            if self.verbose:
                self.info(
                    f"{Fore.BLUE}"
                    f"{pc:#010x} "
                    f"({instruction:#010x}) "
                    f"{assembly}"
                    f"{Style.RESET_ALL}"
                )

            # Send transaction
            tr = InstructionTransaction(
                "tr", None, pc, instruction, register_writes, memory_writes
            )
            self.item_export.write(tr)

    async def monitor_register_writes(self, writes: list[dict]) -> None:
        while self.cfg.interface.get_curr_state() != "INSTR":
            if int(self.cfg.interface.rf_we.value):
                addr = int(self.cfg.interface.rf_waddr.value)
                await RisingEdge(self.cfg.interface.clk)
                val = int(self.cfg.interface.regs[addr].value)

                if addr == 0:
                    assert val == 0, (
                        f"{Fore.RED}Register x0 (zero) must not be written, "
                        f"got value 0x{val:08x}{Style.RESET_ALL}"
                    )
                else:
                    writes.append(
                        {
                            "register": f"x{addr}",
                            "value": val,
                        }
                    )
            else:
                await RisingEdge(self.cfg.interface.clk)

    async def monitor_memory_writes(self, writes: list[dict]) -> None:
        while self.cfg.interface.get_curr_state() != "INSTR":
            if int(self.cfg.interface.ram_we.value):
                phys_addr = int(self.cfg.interface.ram_phys_waddr.value)
                lcl_addr = int(self.cfg.interface.ram_lcl_waddr.value)
                instruction = int(self.cfg.interface.instruction.value)
                funct3 = (instruction >> 12) & 0b111
                byte_count = {0: 1, 1: 2, 2: 4}[funct3]
                byte_shift = 8 * (phys_addr & 0b11)
                value_mask = (1 << (8 * byte_count)) - 1
                preserved_mask = ~(value_mask << byte_shift) & 0xFFFFFFFF
                old_word = (
                    int(self.cfg.interface.ram[lcl_addr].value) if preserved_mask else 0
                )
                await RisingEdge(self.cfg.interface.clk)
                val = int(self.cfg.interface.ram[lcl_addr].value)
                assert ((val ^ old_word) & preserved_mask) == 0, (
                    f"{Fore.RED}Store at 0x{phys_addr:08x} changed untouched bytes: "
                    f"before=0x{old_word:08x}, after=0x{val:08x}, "
                    f"preserved_mask=0x{preserved_mask:08x}{Style.RESET_ALL}"
                )
                val = (val >> byte_shift) & value_mask

                writes.append(
                    {
                        "address": phys_addr,
                        "value": val,
                    }
                )
            else:
                await RisingEdge(self.cfg.interface.clk)

    async def monitor_instruction(self) -> dict:
        # Wait until the CPU leaves INSTR
        while self.cfg.interface.get_curr_state() == "INSTR":
            await RisingEdge(self.cfg.interface.clk)

        register_writes = []
        memory_writes = []

        instruction = int(self.cfg.interface.instruction.value)

        # Run both monitors concurrently
        reg_task = cocotb.start_soon(self.monitor_register_writes(register_writes))
        mem_task = cocotb.start_soon(self.monitor_memory_writes(memory_writes))

        await reg_task
        await mem_task

        return {
            "instruction": instruction,
            "register_writes": register_writes,
            "memory_writes": memory_writes,
        }
