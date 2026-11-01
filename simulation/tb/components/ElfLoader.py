import avl
from colorama import Fore, Style
from tb.utils.elf_utils import load_memory, parse_elf


class ElfLoader(avl.Object):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.memories_map = None
        self.rom = None
        self.ram = None

        self.elf = avl.Factory.get_variable(f"{self.get_full_name()}.elf")

    def load(self):
        assert self.memories_map is not None
        assert self.rom is not None
        assert self.ram is not None
        assert self.elf is not None

        memory_data = parse_elf(self.elf, self.memories_map)

        self.info(f"{Fore.BLUE}Loading ROM{Style.RESET_ALL}")
        # Load DUT ROM
        load_memory(
            self.rom,
            self.memories_map["rom"],
            memory_data["rom"],
        )

        self.info(f"{Fore.BLUE}Loading RAM{Style.RESET_ALL}")
        # Load DUT RAM
        load_memory(
            self.ram,
            self.memories_map["ram"],
            memory_data["ram"],
        )
