import avl


class UartInterface(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.clk = None
        self.rstn = None
        self.uart_rx = None
        self.uart_tx = None
