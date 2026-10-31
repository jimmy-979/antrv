import avl


class scoreboard(avl.Scoreboard):
    def __init___(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)

    # async def run_phase(self) -> None:
    #     """
    #     Runs the scoreboard phase.
    #     """
    #     while True:
    #         self.before_item = await self.before_port.blocking_pop()
    #         self.after_item = await self.after_port.blocking_pop()

    #         res = self.before_item.compare(
    #             self.after_item, verbose=self.verbose, bidirectional=True
    #         )

    #         assert res == True

    #         self.compare_count += 1

    #         self.after_item = None
    #         self.before_item = None
