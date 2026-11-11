import avl
from tb.uart.UartSeqItem import UartSeqItem


class UartSequence(avl.Sequence):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.data = None
        self.inject_error = False

    async def body(self) -> None:
        data_width = self.get_sequencer().cfg.data_width

        item = UartSeqItem("item", self)
        item.data_width = data_width

        await self.start_item(item)
        item.randomize(data=self.data, inject_error=self.inject_error)
        await self.finish_item(item)
