import avl
from tb.uart.UartAgentCfg import UartAgentCfg
from tb.uart.UartConsole import UartConsole
from tb.uart.UartDriver import UartDriver
from tb.uart.UartMonitor import UartMonitor
from tb.uart.UartSequencer import UartSequencer


class UartAgent(avl.Agent):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.cfg = UartAgentCfg("cfg", self)

        self.mon = UartMonitor("mon", self)
        self.drv = UartDriver("drv", self)
        self.sqr = UartSequencer("sqr", self)
        self.tx_console = UartConsole("tx_console", self, "> ")
        self.rx_console = UartConsole("rx_console", self)

        self.mon.cfg = self.cfg
        self.drv.cfg = self.cfg
        self.sqr.cfg = self.cfg

        self.sqr.seq_item_export.connect(self.drv.seq_item_port)
        self.mon.tx_item_export.connect(self.tx_console.item_port)
        self.mon.item_export.connect(self.rx_console.item_port)
