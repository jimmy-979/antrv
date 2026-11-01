import logging
from pathlib import Path

import avl
import cocotb
from avl_files.environment import environment
from colorama import Fore, Style
from sim_utils.elf_utils import *
from sim_utils.sail_utils import *
from sim_utils.test_utils import *

ELF_DIR = "riscv-arch-test/work/antrv/elfs/rv32i/I"
CODE_ELF_DIR = Path(__file__).resolve().parent.parent / "code/build"
_ELFS = [cocotb.Param(elf, name=elf.stem) for elf in Path(ELF_DIR).glob("*.elf")]
_ELFS.extend(cocotb.Param(elf, name=elf.stem) for elf in CODE_ELF_DIR.glob("*.elf"))


class ErrorCounter(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.count = 0

    def emit(self, record):
        self.count += 1


@cocotb.test()
@cocotb.parametrize(elf=_ELFS)
async def test_elf(dut, elf):
    avl.Factory.set_variable("*.hdl", dut)
    avl.Factory.set_variable("*.elf", elf)
    avl.Factory.set_variable("*.sail_ref.config", "act4_config/sail.json")
    avl.Factory.set_variable("*.verbose", True)

    # Disable scoreboard for code ELF files because they exercise peripherals that
    # are not present in sail, so the scoreboard would fail for these tests.
    if elf.resolve().parent == CODE_ELF_DIR.resolve():
        avl.Factory.set_variable("*.disable_scoreboard", True)

    errors = ErrorCounter()
    root_logger = logging.getLogger()
    root_logger.addHandler(errors)

    try:
        env = environment("env", None)
        await env.start()

        assert errors.count == 0, (
            f"{Fore.RED}Simulation logged {errors.count} error(s){Style.RESET_ALL}"
        )
    finally:
        root_logger.removeHandler(errors)
