import avl
from avl_files.antrv_monitor import antrv_monitor
from avl_files.elf_loader import elf_loader
from avl_files.env_config import env_config
from avl_files.sail_reference import sail_reference
from avl_files.scoreboard import scoreboard
from cocotb import start_soon
from cocotb.triggers import RisingEdge
from colorama import Fore, Style
from sim_utils.elf_utils import get_symbol_address, physical_to_local


class environment(avl.Env):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # Create env components
        self.cfg = env_config("cfg", self)
        self.elf_loader = elf_loader("elf_loader", self)
        self.sail_ref = sail_reference("sail_ref", self)
        self.mon = antrv_monitor("mon", self)
        self.scb = scoreboard("scb", self)

        # Get variables
        self.elf = avl.Factory.get_variable(f"{self.get_full_name}.elf")

        # Config env components
        self.elf_loader.memories_map = self.cfg.memory_map
        self.elf_loader.rom = self.cfg.interface.rom
        self.elf_loader.ram = self.cfg.interface.ram

        self.mon.cfg = self.cfg

        # Connect env components
        self.sail_ref.item_export.connect(self.scb.before_port)
        self.mon.item_export.connect(self.scb.after_port)

    async def run_phase(self):
        # Setup clock, timeout
        start_soon(self.clock(self.cfg.interface.clk, self.cfg.clk_freq_mhz))
        await start_soon(
            self.async_reset(
                self.cfg.interface.rstn, self.cfg.rst_duration_ns, "ns", False
            )
        )
        start_soon(self.timeout(self.cfg.timeout_ms, "ms"))

        # Load elf to DUT memory
        self.elf_loader.load()

        # Get tohost address. This will be used to terminate the test
        tohost_phys_addr = get_symbol_address(self.elf, "tohost")
        mem_name, tohost_lcl_addr = physical_to_local(
            tohost_phys_addr, self.cfg.memory_map
        )
        assert mem_name.upper() == "RAM", (
            f"{Fore.RED}Expected to find tohost address in RAM but it was found in {mem_name.upper()}{Style.RESET_ALL}"
        )

        # Wait for tohost to be written
        self.raise_objection()

        try:
            while True:
                tohost_data = int(self.cfg.interface.ram[tohost_lcl_addr >> 2].value)

                if tohost_data == 1:
                    await self.drain_time()
                    self.info(f"{Fore.GREEN}Test passed{Style.RESET_ALL}")
                    break

                elif tohost_data == 3:
                    await self.drain_time()
                    self.error(f"{Fore.RED}Test failed{Style.RESET_ALL}")
                    break

                await RisingEdge(self.cfg.interface.clk)
        finally:
            self.drop_objection()

    async def drain_time(self) -> None:
        for _ in range(2):
            while self.cfg.interface.get_curr_state() == "INSTR":
                await RisingEdge(self.cfg.interface.clk)
            while self.cfg.interface.get_curr_state() != "INSTR":
                await RisingEdge(self.cfg.interface.clk)
        await RisingEdge(self.cfg.interface.clk)
