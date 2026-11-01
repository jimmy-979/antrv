import logging
from collections.abc import Awaitable
from contextlib import contextmanager

import avl
import cocotb
from colorama import Fore, Style


class ErrorCounter(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.count = 0

    def emit(self, record):
        self.count += 1


@contextmanager
def no_logged_errors():
    # Fail the test if anything logged at ERROR level while the block ran
    errors = ErrorCounter()
    root_logger = logging.getLogger()
    root_logger.addHandler(errors)

    try:
        yield
        assert errors.count == 0, (
            f"{Fore.RED}Simulation logged {errors.count} error(s){Style.RESET_ALL}"
        )
    finally:
        root_logger.removeHandler(errors)


async def run_env(env: avl.Env, body: Awaitable) -> None:
    # The test holds the run-phase objection until its own end condition is met
    env.raise_objection()

    async def _body():
        try:
            await body
        finally:
            env.drop_objection()

    cocotb.start_soon(_body())
    await env.start()
