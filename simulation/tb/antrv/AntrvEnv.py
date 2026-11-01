import avl
from cocotb import start_soon
from cocotb.triggers import RisingEdge
from colorama import Fore, Style
from tb.antrv.AntrvEnvCfg import AntrvEnvCfg
from tb.antrv.AntrvMonitor import AntrvMonitor
from tb.components.ElfLoader import ElfLoader
from tb.components.SailReference import SailReference
from tb.components.Scoreboard import Scoreboard
from tb.utils.elf_utils import get_symbol_address, physical_to_local


class AntrvEnv(avl.Env):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # Get variables
        self.disable_scoreboard = avl.Factory.get_variable(
            f"{self.get_full_name}.disable_scoreboard", False
        )
        self.elf = avl.Factory.get_variable(f"{self.get_full_name}.elf")

        # Create env components
        self.cfg = AntrvEnvCfg("cfg", self)
        self.elf_loader = ElfLoader("elf_loader", self)
        self.sail_ref = SailReference("sail_ref", self)
        self.mon = AntrvMonitor("mon", self)
        if not self.disable_scoreboard:
            self.scb = Scoreboard("scb", self)

        # Config env components
        self.elf_loader.memories_map = self.cfg.memory_map
        self.elf_loader.rom = self.cfg.interface.rom
        self.elf_loader.ram = self.cfg.interface.ram

        self.mon.cfg = self.cfg

        # Connect env components
        if not self.disable_scoreboard:
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
