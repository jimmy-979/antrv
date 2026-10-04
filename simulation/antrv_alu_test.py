import random
from enum import Enum

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

ITERATIONS = 20


class AluOp(Enum):
    ALU_ADD = 0
    ALU_SUB = 1


async def test(dut, ina, inb, operation):
    dut.ina_i.value = ina
    dut.inb_i.value = inb
    dut.operation_i.value = operation.value

    cocotb.log.info(
        f"Testing with ina: {hex(ina)}, inb: {hex(inb)}, operation: {operation.name}"
    )

    await RisingEdge(dut.clk_i)
    dut.in_ready_i.value = 1

    await ClockCycles(dut.clk_i, 33)
    assert dut.res_valid_o.value == 1

    if operation == AluOp.ALU_ADD:
        assert dut.res_o.value == (ina + inb) & 0xFFFFFFFF
    elif operation == AluOp.ALU_SUB:
        assert dut.res_o.value == (ina - inb) & 0xFFFFFFFF

    await RisingEdge(dut.clk_i)
    dut.in_ready_i.value = 0


@cocotb.test
async def antrv_alu_test(dut):
    cocotb.start_soon(Clock(dut.clk_i, 40, unit="ns").start())

    cocotb.log.info("Starting test with edge cases")
    for operation in AluOp:
        await test(dut, 0x0, 0x0, operation)
        await test(dut, 0xFFFFFFFF, 0xFFFFFFFF, operation)
        await test(dut, 0x1, 0xFFFFFFFF, operation)
        await test(dut, 0xFFFFFFFF, 0x1, operation)
        await test(dut, 0x80000000, 0x80000000, operation)
        await test(dut, 0x7FFFFFFF, 0x7FFFFFFF, operation)
        await test(dut, 0x80000000, 0x7FFFFFFF, operation)
        await test(dut, 0x7FFFFFFF, 0x80000000, operation)
        await test(dut, 0xFFFFFFFF, 0x0, operation)
        await test(dut, 0x0, 0xFFFFFFFF, operation)

    for iteration in range(ITERATIONS):
        ina = random.randint(0, 2**32 - 1)
        inb = random.randint(0, 2**32 - 1)
        operation = random.choice(list(AluOp))

        cocotb.log.info(f"Iteration: {iteration + 1}")
        await test(dut, ina, inb, operation)
