from enum import Enum

import avl


class State(Enum):
    INSTR = 0
    PC = 1
    ALU = 2
    LATCH_RF = 3


class antrv_interface(avl.Object):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

        self.hdl = avl.Factory.get_variable(f"{self.get_full_name}.hdl")

        self.clk = self.hdl.clk_i
        self.rstn = self.hdl.rst_n_i

        self.rom = self.hdl.inst_rom.mem

        self.ram_we = self.hdl.inst_ram.we_i
        self.ram_phys_waddr = self.hdl.inst_cpu.alu_result
        self.ram_lcl_waddr = self.hdl.inst_ram.waddr_i
        self.ram = self.hdl.inst_ram.mem

        self.pc = self.hdl.inst_cpu.pc
        self.instruction = self.hdl.instr

        self.rf_we = self.hdl.inst_cpu.inst_regfile.we_i
        self.rf_waddr = self.hdl.inst_cpu.inst_regfile.waddr_i
        self.regs = self.hdl.inst_cpu.inst_regfile.mem

        self.state = self.hdl.inst_cpu.state

    def get_curr_state(self) -> str:
        return State(self.state.value).name
