from random import randint

import avl
from cocotb.triggers import Timer
from colorama import Fore, Style


class UartDriver(avl.Driver):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
        self.cfg = None

    async def run_phase(self):
        self.time_per_bit_us = 1e6 / self.cfg.baud_rate
        self.cfg.interface.uart_rx.value = 1

        while True:
            item = await self.seq_item_port.blocking_get()
            self.info(
                f"{Fore.BLUE}Transmitting {hex(item.data)} to DUT{Style.RESET_ALL}"
            )

            if item.inject_error:
                error_bit = randint(0, self.cfg.data_width - 1)

            # Start bit
            self.cfg.interface.uart_rx.value = 0
            await Timer(self.time_per_bit_us, unit="us", round_mode="round")

            # Data bits
            for bit in range(self.cfg.data_width):
                bit_value = (item.data >> bit) & 1

                if item.inject_error and bit == error_bit:
                    bit_value ^= 1

                self.cfg.interface.uart_rx.value = bit_value
                await Timer(self.time_per_bit_us, unit="us", round_mode="round")

            # Stop bit
            self.cfg.interface.uart_rx.value = 1
            await Timer(self.time_per_bit_us, unit="us", round_mode="round")

            item.set_event("done")
