import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _info = ns.AbilityInfo(
        name='Display piped string',
        type=ns.AbilityType.COMPONENT,
    )

    def main(self, **kwargs):
        # always check if we are asked to stop
        while not self.is_stopped():
            try:
                # setup semi-active polling of piped inputs
                if self._poll(0.1):
                    self._view.info("display> {}".format(self._recv()))
            except (IOError, EOFError):
                break
