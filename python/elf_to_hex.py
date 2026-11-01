import argparse
import sys
from pathlib import Path

from elftools.common.exceptions import ELFError
from elftools.elf.elffile import ELFFile


MEMORY_MAP = {
    "rom": (0x80000000, 0x40000),
    "ram": (0x80040000, 0x20000),
}


def memory_images(path: Path) -> dict[str, bytearray]:
    """Load physical ELF segments into the same memory map as code/link.ld."""
    images = {name: bytearray(size) for name, (_, size) in MEMORY_MAP.items()}
    load_segments = 0

    with path.open("rb") as stream:
        elf = ELFFile(stream)
        if (
            elf.elfclass != 32
            or not elf.little_endian
            or elf["e_machine"] != "EM_RISCV"
            or elf["e_type"] != "ET_EXEC"
        ):
            raise ValueError("Expected an executable RV32 little-endian ELF")
        if elf["e_entry"] != MEMORY_MAP["rom"][0]:
            raise ValueError("ELF entry must match the CPU reset address 0x80000000")

        for segment in elf.iter_segments():
            if segment["p_type"] != "PT_LOAD":
                continue

            address = segment["p_paddr"]
            filesz = segment["p_filesz"]
            memsz = segment["p_memsz"]
            if filesz > memsz:
                raise ValueError("ELF load segment file size exceeds memory size")
            if memsz == 0:
                continue

            for name, (base, size) in MEMORY_MAP.items():
                if base <= address and address + memsz <= base + size:
                    data = segment.data()
                    if len(data) != filesz:
                        raise ValueError("Truncated ELF load segment")
                    offset = address - base
                    images[name][offset : offset + memsz] = data + bytes(memsz - filesz)
                    load_segments += 1
                    break
            else:
                raise ValueError(
                    f"ELF load segment does not fit ROM or RAM: "
                    f"0x{address:08x} + 0x{memsz:x} bytes"
                )

    if load_segments == 0:
        raise ValueError("ELF contains no nonempty load segments")
    return images


def write_hex(path: Path, data: bytearray) -> None:
    """Write little-endian 32-bit words, indexed relative to each memory base."""
    with path.open("w", encoding="ascii") as stream:
        stream.write("@00000000\n")
        for offset in range(0, len(data), 4):
            word = int.from_bytes(data[offset : offset + 4], byteorder="little")
            stream.write(f"{word:08x}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert ELF to ROM/RAM readmemh files")
    parser.add_argument("elf", type=Path)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--ram", type=Path, required=True)
    args = parser.parse_args()

    try:
        images = memory_images(args.elf)
        write_hex(args.rom, images["rom"])
        write_hex(args.ram, images["ram"])
    except (OSError, ELFError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
