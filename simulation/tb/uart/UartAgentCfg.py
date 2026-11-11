import avl
from tb.uart.UartInterface import UartInterface


class UartAgentCfg(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # ------------------ UART configuration parameters ------------------ #
        self.data_width = None  # Number of data bits per frame (5, 6, 7, 8, 9)
        self.parity = None  # Parity checking/generation (None, Even, Odd, Mark, Space)
        self.stop_bits = None  # Number of stop bits (1, 1.5, 2)
        self.baud_rate = None  # Communication speed (9600, 38400, 115200, etc.)
        self.clk_freq_mhz = None  # Input clock frequency

        # ---------------------------- Interface ---------------------------- #
        self.interface = UartInterface("interface", self)
