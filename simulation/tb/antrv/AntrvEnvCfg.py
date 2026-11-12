import avl
from tb.antrv.AntrvInterface import AntrvInterface


class AntrvEnvCfg(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # --------------------- Clock frequency in MHz ---------------------- #
        self.clk_freq_mhz = 25

        # ---------------------- Reset duration in ns ----------------------- #
        self.rst_duration_ns = 160

        # ----------------------- Timeout time in ms ------------------------ #
        self.timeout_ms = 50

        # ------------------ GPIO configuration parameters ------------------ #
        self.n_gpios = 8

        # ------------------ UART configuration parameters ------------------ #
        self.data_width = 8
        self.parity = None
        self.stop_bits = 1
        self.baud_rate = 115200

        # ---------------------------- Interface ---------------------------- #
        self.interface = AntrvInterface("interface", self)

        # --------------------------- Memory map ---------------------------- #
        self.memory_map = {
            "rom": {
                "base": 0x80000000,
                "size": 0x40000,
                "permissions": "x",
            },
            "ram": {
                "base": 0x80040000,
                "size": 0x20000,
                "permissions": "rw",
            },
        }
