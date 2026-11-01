import avl
from cocotb import start_soon
from cocotb.triggers import Event
from tb.antrv.AntrvEnvCfg import AntrvEnvCfg
from tb.antrv.AntrvMonitor import AntrvMonitor
from tb.components.ElfLoader import ElfLoader
from tb.components.SailReference import SailReference
from tb.components.Scoreboard import Scoreboard
from tb.gpio.GpioAgent import GpioAgent


class AntrvEnv(avl.Env):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # Get variables
        self.disable_scoreboard = avl.Factory.get_variable(
            f"{self.get_full_name()}.disable_scoreboard", False
        )
        self.elf = avl.Factory.get_variable(f"{self.get_full_name()}.elf")

        # Set once the DUT is out of reset and the ELF is loaded
        self.ready = Event()

        # Create env components
        self.cfg = AntrvEnvCfg("cfg", self)

        self.elf_loader = ElfLoader("elf_loader", self)

        self.gpio_agt = GpioAgent("gpio_agt", self)

        self.mon = AntrvMonitor("mon", self)
        if not self.disable_scoreboard:
            self.sail_ref = SailReference("sail_ref", self)
            self.scb = Scoreboard("scb", self)

        # Config env components
        self.elf_loader.memories_map = self.cfg.memory_map
        self.elf_loader.rom = self.cfg.interface.rom
        self.elf_loader.ram = self.cfg.interface.ram

        self.gpio_agt.cfg.interface.gpios = self.cfg.interface.gpios
        self.gpio_agt.cfg.interface.gpio_drive_data = self.cfg.interface.gpio_drive_data
        self.gpio_agt.cfg.interface.gpio_drive_enable = (
            self.cfg.interface.gpio_drive_enable
        )

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
        self.ready.set()
