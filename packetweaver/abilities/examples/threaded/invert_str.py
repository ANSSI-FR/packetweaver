import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _info = ns.AbilityInfo(
        name='Invert piped string',
        type=ns.AbilityType.COMPONENT,
    )

    def main(self, **kwargs):
        # always check if we are asked to stop
        while not self.is_stopped():
            try:
                # setup semi-active polling of piped inputs
                if self._poll(0.1):
                    s = self._recv()
                    if s == s[::-1]:
                        self._view.warning(
                            'passing the palindrome "{}" '
                            'to be displayed'.format(s)
                        )
                    else:
                        self._view.info(
                            'passing "{}" to be displayed'.format(s)
                        )
                    # forward to the following piped abilities
                    self._send(s[::-1])
            except (IOError, EOFError):
                break
