from random import randint

import avl
from cocotb.types import LogicArray


class GpioSeqItem(avl.SequenceItem):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.n_gpios = None
        self.data = None
        self.mask = None
        self.duration_us = None

        self.set_field_attributes("mask", compare=False)
        self.set_field_attributes("duration_us", compare=False)

    def randomize(self, data=None, mask=None, duration_us=None) -> None:
        assert self.n_gpios, "n_gpios must be set before randomizing"

        if data is not None:
            self.data = data
        else:
            self.data = LogicArray(randint(0, (1 << self.n_gpios) - 1), self.n_gpios)
        self.mask = mask if mask is not None else randint(0, (1 << self.n_gpios) - 1)
        # 72 to 200 us
        self.duration_us = duration_us if duration_us is not None else randint(72, 200)
