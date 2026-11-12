import avl
from tb.gpio.GpioInterface import GpioInterface


class GpioAgentCfg(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # ------------------------- Number of GPIOs ------------------------- #
        self.n_gpios = None

        # ---------------------------- Interface ---------------------------- #
        self.interface = GpioInterface("interface", self)
