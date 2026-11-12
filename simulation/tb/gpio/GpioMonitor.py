import avl
from cocotb.triggers import ValueChange
from colorama import Fore, Style
from tb.gpio.GpioSeqItem import GpioSeqItem


class GpioMonitor(avl.Monitor):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
        self.cfg = None

    async def run_phase(self) -> None:
        gpios = self.cfg.interface.gpios

        previous = gpios.value
        while True:
            await ValueChange(gpios)
            current = gpios.value
            if current != previous:
                self.info(
                    f"{Fore.BLUE}GPIO value changed from {previous} to {current}{Style.RESET_ALL}"
                )

                item = GpioSeqItem("item", self)
                item.n_gpios = self.cfg.n_gpios
                item.data = current
                self.item_export.write(item)

            previous = current
