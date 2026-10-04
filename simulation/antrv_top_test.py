import cocotb
from cocotb.clock import Clock


@cocotb.test
async def antrv_top_test(dut):
    cocotb.start_soon(Clock(dut.clk_i, 40, unit="ns").start())
