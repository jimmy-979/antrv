import avl
from cocotb import start_soon
from cocotb.triggers import Event
from tb.antrv.AntrvEnvCfg import AntrvEnvCfg
from tb.antrv.AntrvMonitor import AntrvMonitor
from tb.components.ElfLoader import ElfLoader
from tb.components.SailReference import SailReference
from tb.components.Scoreboard import Scoreboard
from tb.gpio.GpioAgent import GpioAgent
from tb.uart.UartAgent import UartAgent


class AntrvEnv(avl.Env):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # Get variables
        self.disable_cpu_scoreboard = avl.Factory.get_variable(
            f"{self.get_full_name()}.disable_cpu_scoreboard", False
        )
        self.elf = avl.Factory.get_variable(f"{self.get_full_name()}.elf")

        # Set once the DUT is out of reset and the ELF is loaded
        self.ready = Event()

        # Create env components
        self.cfg = AntrvEnvCfg("cfg", self)

        self.elf_loader = ElfLoader("elf_loader", self)

        self.gpio_agt = GpioAgent("gpio_agt", self)
        self.uart_agt = UartAgent("uart_agt", self)

        self.cpu_mon = AntrvMonitor("cpu_mon", self)
        if not self.disable_cpu_scoreboard:
            self.sail_ref = SailReference("sail_ref", self)
            self.cpu_scb = Scoreboard("cpu_scb", self)

        self.uart_scb = Scoreboard("uart_scb", self)

        # Config env components
        self.elf_loader.memories_map = self.cfg.memory_map
        self.elf_loader.rom = self.cfg.interface.rom
        self.elf_loader.ram = self.cfg.interface.ram

        self.gpio_agt.cfg.n_gpios = self.cfg.n_gpios

        self.uart_agt.cfg.data_width = self.cfg.data_width
        self.uart_agt.cfg.parity = self.cfg.parity
        self.uart_agt.cfg.stop_bits = self.cfg.stop_bits
        self.uart_agt.cfg.baud_rate = self.cfg.baud_rate
        self.uart_agt.cfg.clk_freq_mhz = self.cfg.clk_freq_mhz

        self.gpio_agt.cfg.interface = self.cfg.interface
        self.uart_agt.cfg.interface = self.cfg.interface

        self.cpu_mon.cfg = self.cfg

        # Connect env components
        if not self.disable_cpu_scoreboard:
            self.sail_ref.item_export.connect(self.cpu_scb.before_port)
            self.cpu_mon.item_export.connect(self.cpu_scb.after_port)

        self.uart_agt.sqr.seq_item_export.connect(self.uart_scb.before_port)
        self.uart_agt.mon.item_export.connect(self.uart_scb.after_port)

    async def run_phase(self):
        start_soon(self.timeout(self.cfg.timeout_ms, "ms"))
        start_soon(self.ticker(5, ".", "ms"))
        # Setup clock
        start_soon(self.clock(self.cfg.interface.clk, self.cfg.clk_freq_mhz))
        await start_soon(
            self.async_reset(
                self.cfg.interface.rstn, self.cfg.rst_duration_ns, "ns", False
            )
        )

        # Load elf to DUT memory
        self.elf_loader.load()
        self.ready.set()
