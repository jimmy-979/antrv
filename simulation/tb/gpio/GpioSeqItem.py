from random import randint

import avl


class GpioSeqItem(avl.SequenceItem):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.data = None
        self.mask = None
        self.duration_ns = None

    def randomize(self, data=None, mask=None, duration_ns=None) -> None:
        self.data = data if data is not None else randint(0, 2**32 - 1)
        self.mask = mask if mask is not None else randint(0, 2**32 - 1)
        self.duration_ns = duration_ns if duration_ns is not None else randint(1, 100)
