from random import randint

import avl
from tb.gpio.GpioSeqItem import GpioSeqItem


class GpioSequence(avl.Sequence):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.gpio_num = None
        self.num_items = randint(1, 10)
        self.data = None
        self.mask = None
        self.duration_ns = None

    async def body(self) -> None:
        assert self.gpio_num is not None, (
            "gpio_num must be set before running the sequence"
        )

        for idx in range(self.num_items):
            item = GpioSeqItem(f"item{idx}", self)
            await self.start_item(item)

            _data = (
                randint(0, (1 << self.gpio_num) - 1) if self.data is None else self.data
            )
            _mask = (
                randint(0, (1 << self.gpio_num) - 1) if self.mask is None else self.mask
            )
            _duration_ns = (
                randint(1, 100) if self.duration_ns is None else self.duration_ns
            )

            item.randomize(data=_data, mask=_mask, duration_ns=_duration_ns)

            await self.finish_item(item)
