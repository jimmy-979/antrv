import avl


class GpioSequencer(avl.Sequencer):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
