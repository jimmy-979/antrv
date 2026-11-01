import re
import subprocess
from pathlib import Path

HEX = r"0x[0-9a-fA-F]+"

MEM_RE = re.compile(
    rf"^\s*mem\[(?P<kind>[A-Za-z]+),\s*(?P<address>{HEX})\]"
    rf"\s*(?P<operator><-|->)\s*(?P<value>{HEX})\s*$"
)

INSN_RE = re.compile(
    rf"^\[(?P<index>\d+)\]\s+\[(?P<mode>[^\]]+)\]:\s*"
    rf"(?P<pc>{HEX})\s+\((?P<word>{HEX})\)\s+"
    rf"(?P<tail>.*)$"
)

REG_RE = re.compile(rf"^\s*(?P<register>x\d+)\s*<-\s*(?P<value>{HEX})\s*$")

CSR_RE = re.compile(
    rf"^\s*CSR\s+(?P<name>\S+)\s+\((?P<address>{HEX})\)"
    rf"\s*<-\s*(?P<value>{HEX})\s*$"
)


def run_sail(elf_path: Path, config_path: Path) -> str:
    """Run the Sail RISC-V reference simulator and capture its trace."""

    result = subprocess.run(
        [
            "sail_riscv_sim",
            "--trace",
            "--config",
            str(config_path),
            str(elf_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Sail exited with code {result.returncode}:\n{result.stdout}"
        )

    return result.stdout


def parse_sail_trace(trace: str) -> dict:
    """Parse the textual execution trace produced by sail_riscv_sim."""
    result = {
        "metadata": {},
        "instructions": [],
        "csr_writes": [],
        "preamble_memory": [],
        "orphan_register_writes": [],
        "unmatched_fetches": [],
    }

    pending_fetches = []
    current_instruction = None

    for raw_line in trace.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # Parse simulator metadata.
        if line.startswith("HTIF located at "):
            result["metadata"]["htif"] = int(line.split()[-1], 16)
            continue

        if line.startswith("begin_signature:"):
            result["metadata"]["begin_signature"] = int(
                line.split(":", 1)[1].strip(), 16
            )
            continue

        if line.startswith("end_signature:"):
            result["metadata"]["end_signature"] = int(line.split(":", 1)[1].strip(), 16)
            continue

        if line.startswith("Entry point:"):
            result["metadata"]["entry_point"] = int(line.split(":", 1)[1].strip(), 16)
            continue

        # Parse memory events.
        match = MEM_RE.match(line)
        if match:
            event = {
                "kind": match.group("kind").upper(),
                "address": int(match.group("address"), 16),
                "operator": match.group("operator"),
                "value": int(match.group("value"), 16),
            }

            if event["kind"] == "X":
                # Instruction fetches are usually printed before the
                # corresponding instruction line.
                pending_fetches.append(event)

            elif current_instruction is not None:
                current_instruction["memory_accesses"].append(event)

            else:
                result["preamble_memory"].append(event)

            continue

        # Parse instruction execution lines.
        match = INSN_RE.match(line)
        if match:
            tail = match.group("tail").strip()

            # Separate the disassembly from the optional symbol.
            parts = re.split(r"\s{2,}", tail, maxsplit=1)

            instruction = {
                "index": int(match.group("index")),
                "mode": match.group("mode"),
                "pc": int(match.group("pc"), 16),
                "word": int(match.group("word"), 16),
                "disassembly": parts[0],
                "symbol": parts[1] if len(parts) > 1 else None,
                "fetch": None,
                "register_writes": [],
                "memory_accesses": [],
                "csr_writes": [],
            }

            # Match the instruction with its fetch event.
            for i, fetch in enumerate(pending_fetches):
                if fetch["address"] == instruction["pc"]:
                    instruction["fetch"] = pending_fetches.pop(i)
                    break

            result["instructions"].append(instruction)
            current_instruction = instruction
            continue

        # Parse integer register writes.
        match = REG_RE.match(line)
        if match:
            event = {
                "register": match.group("register"),
                "value": int(match.group("value"), 16),
            }

            if current_instruction is not None:
                current_instruction["register_writes"].append(event)
            else:
                result["orphan_register_writes"].append(event)

            continue

        # Parse CSR writes.
        match = CSR_RE.match(line)
        if match:
            event = {
                "name": match.group("name"),
                "address": int(match.group("address"), 16),
                "value": int(match.group("value"), 16),
            }

            result["csr_writes"].append(event)

            if current_instruction is not None:
                current_instruction["csr_writes"].append(event)

    result["unmatched_fetches"] = pending_fetches

    return result
