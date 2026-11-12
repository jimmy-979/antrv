from pathlib import Path
from random import randint

import avl
import cocotb
from cocotb.triggers import RisingEdge, Timer
from colorama import Fore, Style
from tb.antrv.AntrvEnv import AntrvEnv
from tb.gpio.GpioSequence import GpioSequence
from tb.uart.UartSequence import UartSequence
from tb.utils.elf_utils import *
from tb.utils.sail_utils import *
from tb.utils.test_utils import *

ACT4_ELF_DIR = "riscv-arch-test/work/antrv/elfs/rv32i/I"
_ACT4_ELFS = [
    cocotb.Param(elf, name=elf.stem) for elf in Path(ACT4_ELF_DIR).glob("*.elf")
]

CODE_DIR = "../code/build"
_GPIO_ELFS = [
    cocotb.Param(elf, name=elf.stem) for elf in Path(CODE_DIR).glob("*gpio*.elf")
]
_UART_ELFS = [
    cocotb.Param(elf, name=elf.stem) for elf in Path(CODE_DIR).glob("*uart*.elf")
]


@cocotb.test()
@cocotb.parametrize(elf=_ACT4_ELFS)
async def test_elf(dut, elf):
    avl.Factory.set_variable("*.hdl", dut)
    avl.Factory.set_variable("*.elf", elf)
    avl.Factory.set_variable("*.sail_ref.config", "act4_config/sail.json")
    avl.Factory.set_variable("*.verbose", True)

    with no_logged_errors():
        env = AntrvEnv("env", None)
        itf = env.cfg.interface

        async def drain_time():
            # Let the final instructions retire before ending the test
            for _ in range(2):
                while itf.get_curr_state() == "INSTR":
                    await RisingEdge(itf.clk)
                while itf.get_curr_state() != "INSTR":
                    await RisingEdge(itf.clk)
            await RisingEdge(itf.clk)

        async def wait_for_tohost():
            await env.ready.wait()

            tohost_phys_addr = get_symbol_address(elf, "tohost")
            mem_name, tohost_lcl_addr = physical_to_local(
                tohost_phys_addr, env.cfg.memory_map
            )
            assert mem_name.upper() == "RAM", (
                f"{Fore.RED}Expected to find tohost address in RAM but it was found in {mem_name.upper()}{Style.RESET_ALL}"
            )

            while True:
                tohost_data = int(env.cfg.interface.ram[tohost_lcl_addr >> 2].value)

                if tohost_data == 1:
                    await drain_time()
                    env.info(f"{Fore.GREEN}Test passed{Style.RESET_ALL}")
                    break

                elif tohost_data == 3:
                    await drain_time()
                    env.error(f"{Fore.RED}Test failed{Style.RESET_ALL}")
                    break

                await RisingEdge(env.cfg.interface.clk)

        await run_env(env, wait_for_tohost())


@cocotb.test()
@cocotb.parametrize(elf=_GPIO_ELFS)
async def test_gpio(dut, elf):
    avl.Factory.set_variable("*.hdl", dut)
    avl.Factory.set_variable("*.elf", elf)
    avl.Factory.set_variable("*.disable_cpu_scoreboard", True)

    with no_logged_errors():
        env = AntrvEnv("env", None)

        async def stimulus():
            await env.ready.wait()

            for i in range(randint(50, 100)):
                await Timer(randint(1_000, 100_000), unit="ps")

                cocotb.log.info(f"{Fore.BLUE}Iteration {i + 1}{Style.RESET_ALL}")

                seq = GpioSequence("seq", None)
                input_value = randint(0, 0xF)
                seq.data = input_value
                seq.set_sequencer(env.gpio_agt.sqr)
                await seq.start()

                # gpio_c_test.c configures pins [3:0] as inputs and mirrors
                # their value onto pins [7:4].  The sequence has completed
                # here, so the external driver has released pins [3:0].
                expected_output = input_value << 4
                actual_output = int(env.cfg.interface.gpios.value) & 0xF0
                assert actual_output == expected_output, (
                    f"{Fore.RED}GPIO mirror mismatch: drove {input_value:04b}; "
                    f"expected output {expected_output >> 4:04b}, got "
                    f"{actual_output >> 4:04b}{Style.RESET_ALL}"
                )

        await run_env(env, stimulus())


@cocotb.test()
@cocotb.parametrize(elf=_UART_ELFS)
async def test_uart(dut, elf):
    avl.Factory.set_variable("*.hdl", dut)
    avl.Factory.set_variable("*.elf", elf)
    avl.Factory.set_variable("*.disable_cpu_scoreboard", True)

    with no_logged_errors():
        env = AntrvEnv("env", None)

        async def stimulus():
            await env.ready.wait()

            for i in range(randint(100, 200)):
                await Timer(randint(0, 100_000), unit="ps")

                cocotb.log.info(f"{Fore.BLUE}Iteration {i + 1}{Style.RESET_ALL}")

                seq = UartSequence("seq", None)
                seq.set_sequencer(env.uart_agt.sqr)
                await seq.start()

        await run_env(env, stimulus())
