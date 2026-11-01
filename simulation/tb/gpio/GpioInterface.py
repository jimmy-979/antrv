import avl


class GpioInterface(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.gpios = None
        self.gpio_drive_data = None
        self.gpio_drive_enable = None
