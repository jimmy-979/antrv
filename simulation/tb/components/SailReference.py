import os
from pathlib import Path

import avl
from avl import Port
from tb.components.InstructionTransaction import InstructionTransaction
from tb.utils.sail_utils import parse_sail_trace, run_sail


class SailReference(avl.Component):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        # Get elf and sail configuration file
        elf = avl.Factory.get_variable(f"{self.get_full_name()}.elf")
        sail_config = avl.Factory.get_variable(f"{self.get_full_name()}.config")

        # Get trace from Sail
        trace = run_sail(elf, sail_config)

        # Save trace log (optional)
        trace_dir = Path(f"{os.getenv('SIM_BUILD')}/trace")
        trace_dir.mkdir(parents=True, exist_ok=True)
        Path(trace_dir / f"{Path(elf).stem}.log").write_text(trace)

        # Parse trace log
        self.parsed = parse_sail_trace(trace)
        self.debug(f"Sail trace metadata: {self.parsed['metadata']}")

        self.item_export = Port("item_export", self)

    async def run_phase(self):
        for insn in self.parsed["instructions"]:
            pc = insn["pc"]
            instruction = insn["word"]
            register_writes = insn["register_writes"]

            memory_writes = []
            for memory_access in insn["memory_accesses"]:
                if memory_access["kind"] == "W":
                    memory_writes.append(
                        {
                            "address": memory_access["address"],
                            "value": memory_access["value"],
                        }
                    )

            if insn["csr_writes"]:
                raise ValueError("CSR write checks haven't implemented yet")

            tr = InstructionTransaction(
                "tr", None, pc, instruction, register_writes, memory_writes
            )
            self.item_export.write(tr)
