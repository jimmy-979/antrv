import avl


class InstructionTransaction(avl.Object):
    def __init__(
        self,
        name: str,
        parent,
        pc: int,
        instruction: int,
        register_writes: list[dict],
        memory_writes: list[dict],
    ):
        super().__init__(name, parent)

        self.pc = pc
        self.instruction = instruction
        self.register_writes = register_writes
        self.memory_writes = memory_writes
