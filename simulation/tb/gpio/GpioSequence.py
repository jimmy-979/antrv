import avl
from tb.gpio.GpioSeqItem import GpioSeqItem


class GpioSequence(avl.Sequence):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.data = None
        self.mask = 0xF
        self.duration_us = None

    async def body(self) -> None:
        n_gpios = self.get_sequencer().cfg.n_gpios

        item = GpioSeqItem("item", self)
        item.n_gpios = n_gpios

        await self.start_item(item)
        item.randomize(data=self.data, mask=self.mask, duration_us=self.duration_us)
        await self.finish_item(item)
