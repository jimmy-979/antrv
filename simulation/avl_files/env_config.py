import avl
from avl_files.antrv_interface import antrv_interface


class env_config(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        # --------------------- Clock frequency in MHz ---------------------- #
        self.clk_freq_mhz = 25

        # --------------------- Clock frequency in MHz ---------------------- #
        self.rst_duration_ns = 160

        # ----------------------- Timeout time in ns ------------------------ #
        self.timeout_ms = 50

        # ---------------------------- Interface ---------------------------- #
        self.interface = antrv_interface("interface", self)

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
