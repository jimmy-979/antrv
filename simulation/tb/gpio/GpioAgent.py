import avl
from tb.gpio.GpioAgentCfg import GpioAgentCfg
from tb.gpio.GpioDriver import GpioDriver
from tb.gpio.GpioMonitor import GpioMonitor
from tb.gpio.GpioSequencer import GpioSequencer


class GpioAgent(avl.Agent):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.cfg = GpioAgentCfg("cfg", self)

        self.mon = GpioMonitor("mon", self)
        self.drv = GpioDriver("drv", self)
        self.seq = GpioSequencer("seq", self)

        self.mon.cfg = self.cfg
        self.drv.cfg = self.cfg

        self.seq.seq_item_export.connect(self.drv.seq_item_port)
