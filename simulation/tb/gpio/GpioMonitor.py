import avl
from cocotb.triggers import ValueChange
from colorama import Fore, Style


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
                self.item_export.write(current)
            previous = current
