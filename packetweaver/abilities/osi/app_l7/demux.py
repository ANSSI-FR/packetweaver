# coding: utf8
import threading

import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = []

    _info = ns.AbilityInfo(
        name='Demux',
        description='Demultiplex a series of datagrammes, based on a prefix',
        authors=['Florian Maury', ],
        tags=[ns.Tag.EXAMPLE],
        type=ns.AbilityType.COMPONENT
    )

    def main(self, demux, quiet=True):
        if len([prefix for prefix in demux.keys() if len(prefix) != 1]) > 0:
            self._view.error('Prefixes must be one char long')

        try:
            while not self.is_stopped():
                if self._poll(0.1):
                    s = self._recv()
                    if s[0] in demux:
                        demux[s[0]].send(s[1:])
                    elif not quiet:
                        self._view.warning('Invalid prefix: {0:1s}'.format(s[0]))
        except (IOError, EOFError):
            pass
