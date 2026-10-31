from pathlib import Path

import cocotb
from colorama import Fore, Style
from elftools.elf.elffile import ELFFile


def find_memory(address, size, memories_table):
    """Return the memory containing [address, address + size)."""

    end = address + size

    for name, memory in memories_table.items():
        mem_start = memory["base"]
        mem_end = mem_start + memory["size"]

        if address >= mem_start and end <= mem_end:
            return name, memory

    return None, None


def physical_to_local(address, memories_table):
    """
    Translate a physical address into a memory name and local byte offset.

    Returns:
        (memory_name, local_offset)

    Raises:
        ValueError: If the address does not belong to any configured memory.
    """

    memory_name, memory = find_memory(address, 1, memories_table)

    if memory is None:
        raise ValueError(f"No memory contains address 0x{address:08x}")

    local_offset = address - memory["base"]

    return memory_name, local_offset


def dump_data(address, data, width=16):
    """Dump binary data as hexadecimal bytes."""

    for offset in range(0, len(data), width):
        chunk = data[offset : offset + width]

        hex_data = " ".join(f"{byte:02x}" for byte in chunk)

        cocotb.log.debug(f"    0x{address + offset:08x}: {hex_data}")


def parse_elf(path, memories_table, verbose=False):
    """
    Parse an ELF file and return its memory initialization data.

    Returns:
        {
            "rom": [
                (address, data),
                ...
            ],
            "ram": [
                (address, data),
                ...
            ],
        }
    """

    path = Path(path)

    memories = {name: [] for name in memories_table}

    with path.open("rb") as f:
        elf = ELFFile(f)

        cocotb.log.debug("")
        cocotb.log.debug("=" * 80)
        cocotb.log.info(f"{Fore.BLUE}Parsing ELF: {path}{Style.RESET_ALL}")

        cocotb.log.debug("")
        cocotb.log.debug(f"Class:   {elf.elfclass}-bit")
        cocotb.log.debug(f"Machine: {elf['e_machine']}")
        cocotb.log.debug(f"Entry:   0x{elf.header['e_entry']:08x}")

        for segment in elf.iter_segments():
            if segment["p_type"] != "PT_LOAD":
                continue

            addr = segment["p_paddr"]
            filesz = segment["p_filesz"]
            memsz = segment["p_memsz"]

            memory_name, memory = find_memory(addr, memsz, memories_table)

            cocotb.log.debug("")
            cocotb.log.debug(
                f"LOAD SEGMENT @ 0x{addr:08x} (filesz=0x{filesz:x} memsz=0x{memsz:x})"
            )

            if memory is None:
                raise ValueError(
                    f"Segment does not fit in any memory: "
                    f"0x{addr:08x} - "
                    f"0x{addr + memsz - 1:08x}"
                )

            cocotb.log.debug(f"Memory: {memory_name.upper()}")

            # --------------------------------------------------
            # Sections
            # --------------------------------------------------

            cocotb.log.debug("Sections:")

            segment_start = addr
            segment_end = addr + memsz

            for section in elf.iter_sections():
                section_addr = section["sh_addr"]
                section_size = section["sh_size"]

                if section_size == 0:
                    continue

                section_end = section_addr + section_size

                if section_addr < segment_end and section_end > segment_start:
                    cocotb.log.debug(
                        f"  {section.name:20} "
                        f"0x{section_addr:08x} - "
                        f"0x{section_end - 1:08x} "
                        f"({section_size} bytes)"
                    )

            # --------------------------------------------------
            # Data stored in ELF
            # --------------------------------------------------

            data = segment.data()

            if filesz:
                memories[memory_name].append((addr, data))

                if verbose:
                    cocotb.log.debug("Data:")
                    dump_data(addr, data)

            # --------------------------------------------------
            # Zero-filled portion
            # --------------------------------------------------

            zero_size = memsz - filesz

            if zero_size:
                zero_address = addr + filesz

                memories[memory_name].append(
                    (
                        zero_address,
                        b"\x00" * zero_size,
                    )
                )

                cocotb.log.debug("")
                cocotb.log.debug(
                    f"Zero-fill: "
                    f"0x{zero_address:08x} - "
                    f"0x{addr + memsz - 1:08x} "
                    f"({zero_size} bytes)"
                )

        cocotb.log.debug("=" * 80)
        cocotb.log.debug("")

    return memories


def load_memory(dut_memory, memory, segments):
    """
    Load parsed ELF segments into a 32-bit word-addressed DUT memory.

    The DUT memory is assumed to contain 32-bit words and the
    target CPU is little-endian.
    """

    for address, data in segments:
        offset = address - memory["base"]

        if offset < 0:
            raise ValueError(
                f"Address 0x{address:08x} is below memory base 0x{memory['base']:08x}"
            )

        if offset + len(data) > memory["size"]:
            raise ValueError(
                f"Data exceeds {memory}: address=0x{address:08x}, size=0x{len(data):x}"
            )

        if offset % 4:
            raise ValueError(f"Unaligned address: 0x{address:08x}")

        # Pad to a complete 32-bit word.
        if len(data) % 4:
            data += b"\x00" * (-len(data) % 4)

        word_index = offset // 4

        for i in range(0, len(data), 4):
            word = int.from_bytes(
                data[i : i + 4],
                byteorder="little",
            )

            dut_memory[word_index + i // 4].value = word


def get_symbol_address(
    elf_path: str | Path,
    symbol_name: str,
) -> int:
    """Return the address of a symbol in an ELF file."""
    with open(elf_path, "rb") as elf_file:
        elf = ELFFile(elf_file)

        for section in elf.iter_sections():
            if not hasattr(section, "get_symbol_by_name"):
                continue

            symbols = section.get_symbol_by_name(symbol_name)

            if symbols:
                return symbols[0]["st_value"]

    raise ValueError(f"Symbol '{symbol_name}' not found in '{elf_path}'")
