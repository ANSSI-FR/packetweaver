import threading
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.StrOpt('prefix', default='', comment='Prefix to the echo reply'),
        ns.StrOpt('client_info',
                  default='',
                  comment='Information about the client connected '
                          'to the socket')
    ]

    _info = ns.AbilityInfo(
        name='Echo Server',
        description='echoes back the received messages with a prefix and '
                    'the information about the connected client',
        authors=['Florian Maury', ],
        tags=[ns.Tag.EXAMPLE],
        type=ns.AbilityType.COMPONENT
    )

    def __init__(self, *args, **kwargs):
        super(Ability, self).__init__(*args, **kwargs)
        self._stop_evt = threading.Event()

    def stop(self):
        ns.ThreadedAbilityBase.stop(self)
        self._stop_evt.set()

    def main(self):
        while not self._stop_evt.is_set():
            try:
                if self._poll(0.1):
                    s = self._recv()
                    self._send(self.prefix.format(self.client_info) + s)
            except (IOError, EOFError):
                self._stop_evt.set()
