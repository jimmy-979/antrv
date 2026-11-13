import avl
from tb.uart.UartSeqItem import UartSeqItem


class UartTxByteSequence(avl.Sequence):
    def __init__(
        self, name: str, parent: avl.Component, data: int | None = None
    ) -> None:
        super().__init__(name, parent)

        self.data = data
        self.inject_error = False

    async def body(self) -> None:
        data_width = self.get_sequencer().cfg.data_width

        item = UartSeqItem("item", self)
        item.data_width = data_width

        await self.start_item(item)
        item.randomize(data=self.data, inject_error=self.inject_error)
        await self.finish_item(item)


class UartTxWordSequence(avl.Sequence):
    def __init__(
        self, name: str, parent: avl.Component, tx_word: bytes | None = None
    ) -> None:
        super().__init__(name, parent)

        self.tx_word = tx_word

    async def body(self) -> None:
        for byte in self.tx_word:
            data_width = self.get_sequencer().cfg.data_width

            item = UartSeqItem("item", self)
            item.data_width = data_width

            await self.start_item(item)
            item.randomize(data=byte, inject_error=False)
            await self.finish_item(item)
