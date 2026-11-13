import avl
from avl import Port
from cocotb import start_soon
from cocotb.triggers import FallingEdge, Timer
from colorama import Fore, Style
from tb.uart.UartSeqItem import UartSeqItem


class UartMonitor(avl.Monitor):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
        self.cfg = None
        self.tx_item_export = Port("tx_item_export", self)
        self.verbose = avl.Factory.get_variable("*.uart_verbose", False)

    async def run_phase(self):
        self.time_per_bit_us = 1e6 / self.cfg.baud_rate
        self.cfg.interface.uart_rx.value = 1
        start_soon(self.monitor_rx())
        await self.monitor_tx()

    async def monitor_rx(self):
        while True:
            await FallingEdge(self.cfg.interface.uart_rx)

            # Wait for half a bit time to sample in the middle of the bit
            await Timer(self.time_per_bit_us / 2, unit="us", round_mode="round")
            if self.cfg.interface.uart_rx.value != 0:
                continue

            # Read the data bits
            data = 0
            for i in range(self.cfg.data_width):
                await Timer(self.time_per_bit_us, unit="us", round_mode="round")
                data |= int(self.cfg.interface.uart_rx.value) << i

            # Read the stop bit
            await Timer(1.5 * self.time_per_bit_us, unit="us", round_mode="round")

            if self.verbose:
                self.info(f"{Fore.BLUE}DUT received {hex(data)}{Style.RESET_ALL}")

            item = UartSeqItem("item", self)
            item.data_width = self.cfg.data_width
            item.data = data
            item.inject_error = False
            self.item_export.write(item)

    async def monitor_tx(self):
        while True:
            await FallingEdge(self.cfg.interface.uart_tx)

            # Wait for half a bit time to sample in the middle of the bit
            await Timer(self.time_per_bit_us / 2, unit="us", round_mode="round")
            if self.cfg.interface.uart_tx.value != 0:
                continue

            # Read the data bits
            data = 0
            for i in range(self.cfg.data_width):
                await Timer(self.time_per_bit_us, unit="us", round_mode="round")
                data |= int(self.cfg.interface.uart_tx.value) << i

            # Read the stop bit
            await Timer(1.5 * self.time_per_bit_us, unit="us", round_mode="round")

            if self.verbose:
                self.info(f"{Fore.BLUE}DUT transmitted {chr(data)!r}{Style.RESET_ALL}")

            item = UartSeqItem("item", self)
            item.data_width = self.cfg.data_width
            item.data = data
            item.inject_error = False
            self.tx_item_export.write(item)
