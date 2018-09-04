import socket
import threading
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.ChoiceOpt('protocol', ['IPv4', 'IPv6'], comment='IPv4 or IPv6'),
        ns.IpOpt(ns.OptNames.IP_SRC,
                 default=None,
                 comment='Local (Source) IP',
                 optional=True),
        ns.IpOpt(ns.OptNames.IP_DST,
                 default='127.0.0.1',
                 comment='Remote (Destination) IP'),
        ns.PortOpt(ns.OptNames.PORT_SRC,
                   default=0,
                   comment='Local (Source) Port (0 = Random Port)'),
        ns.PortOpt(ns.OptNames.PORT_DST,
                   default=0,
                   comment='Remote (Destination) Port'),
        ns.OptionTemplateEntry(lambda x: 0 <= x <= 10,
                               ns.NumOpt('timeout',
                                         default=5,
                                         comment='Connect Timeout'))
    ]

    _info = ns.AbilityInfo(
        name='TCP Client',
        description='Sends and receives segments',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L4],
        type=ns.AbilityType.COMPONENT
    )

    @staticmethod
    def _forward_outgoing(sock, stop_evt, poller, receiver):
        while not stop_evt.is_set():
            if poller(0.1):
                try:
                    s = receiver()
                except EOFError:
                    break
                sock.send(str(s))

    @staticmethod
    def _forward_incoming(sock, stop_evt, sender, stopper):
        # Timeout is set back to 0.1 second for polling purposes
        sock.settimeout(0.1)
        while not stop_evt.is_set():
            try:
                s = sock.recv(65535)
            except socket.timeout:
                continue
            if len(s) == 0:
                # Socket is closed!
                break
            sender(s)
        stopper()

    def main(self):
        if self._is_sink() or self._is_source():
            raise Exception(
                'This ability must be connected through pipes '
                'to other abilities!'
            )

        if self.protocol == 'IPv4':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        s.bind(('' if isinstance(self.ip_src, type(None))
                else self.ip_src, self.port_src))
        s.settimeout(self.timeout)
        s.connect((self.ip_dst, self.port_dst))

        stop_evt = threading.Event()

        out_thr = threading.Thread(target=self._forward_outgoing,
                                   args=(s, stop_evt, self._poll, self._recv))
        out_thr.start()

        in_thr = threading.Thread(target=self._forward_incoming,
                                  args=(s, stop_evt, self._send, self.stop))
        in_thr.start()

        self._wait()

        stop_evt.set()

        out_thr.join()
        in_thr.join()
        s.close()
