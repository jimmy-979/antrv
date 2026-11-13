import avl
from avl import List
from colorama import Fore, Style
from tb.uart.UartSeqItem import UartSeqItem


class UartConsole(avl.Component):
    def __init__(
        self, name: str, parent: avl.Component, print_prefix: str = ""
    ) -> None:
        super().__init__(name, parent)
        self.buffer = bytearray()
        self.item_port = List()
        self.print_prefix = print_prefix

    async def run_phase(self):
        while True:
            data = await self.item_port.blocking_get()
            self.write(data)

    def write(self, item: UartSeqItem) -> None:
        data = bytes([item.data])

        if data == b"\r":
            return

        if data == b"\n":
            self.info(
                f"{Fore.BLUE}{self.print_prefix}{self.buffer.decode('utf-8', errors='replace')}{Style.RESET_ALL}"
            )
            self.buffer.clear()
            return

        self.buffer.extend(data)
