# coding: utf8
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _info = ns.AbilityInfo(
        name='Debug Packets',
        description='Prints received packets',
        authors=['Florian Maury', ],
        tags=[ns.Tag.EXAMPLE],
        type=ns.AbilityType.COMPONENT
    )

    def main(self):
        while not self.is_stopped():
            try:
                if self._poll(0.1):
                    print(self._recv().encode('hex'))
            except (IOError, EOFError):
                break
