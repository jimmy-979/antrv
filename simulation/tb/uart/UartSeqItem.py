from random import randint

import avl


class UartSeqItem(avl.SequenceItem):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.data_width = None
        self.data = None
        self.inject_error = None

    def randomize(self, data=None, inject_error=None) -> None:
        assert self.data_width is not None, (
            "data_width must be set before randomizing data"
        )

        if data:
            self.data = data
        else:
            self.data = randint(0, (1 << self.data_width) - 1)

        if inject_error is not None:
            self.inject_error = inject_error
        else:
            self.inject_error = bool(randint(0, 1))
