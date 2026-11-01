import avl
from cocotb.triggers import Timer


class GpioDriver(avl.Driver):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
        self.cfg = None

    async def run_phase(self):
        all_pins = (1 << len(self.cfg.interface.gpios)) - 1

        # Start with every pin released so the DUT owns the bus
        self.cfg.interface.gpio_drive_enable.value = 0
        self.cfg.interface.gpio_drive_data.value = 0

        while True:
            item = await self.seq_item_port.blocking_get()
            mask = item.mask & all_pins

            self.cfg.interface.gpio_drive_data.value = item.data & mask
            self.cfg.interface.gpio_drive_enable.value = mask

            await Timer(item.duration_ns, unit="ns")

            self.cfg.interface.gpio_drive_enable.value = 0

            item.set_event("done")
