# coding: utf8
import packetweaver.core.ns as ns
import struct

try:
    import scapy.layers.dns as scapy_dns
    import scapy.layers.l2 as l2
    import scapy.config
    import scapy.layers.inet as scapy_inet
    import scapy.layers.inet6 as scapy_inet6
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.BoolOpt('quiet', default=True, comment='Whether we should log stuff on error'),
    ]

    _info = ns.AbilityInfo(
        name='DNS Metadata Extractor',
        description='Reads a Ether frame containing DNS and writes len(Ether to UDP/TCP) + Ether to UDP/TCP + DNS',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L5, ns.Tag.THREADED, ns.Tag.DNS],
        type=ns.AbilityType.COMPONENT
    )

    _dependencies = []

    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not HAS_SCAPY:
            l.append('Scapy support missing or broken. Please install scapy or proceed to an update.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l

    def main(self):
        try:
            while not self.is_stopped():
                if self._poll(0.1):
                    s = self._recv()
                    try:
                        m = l2.Ether(s)
                        data = str(m[scapy_dns.DNS])
                        if m.haslayer(scapy_inet.UDP):
                            m[scapy_inet.UDP].remove_payload()
                        else:
                            m[scapy_inet.UDP].remove_payload()
                        metadata = str(m)
                        self._send(
                            '{}{}{}'.format(
                                struct.pack('!H', len(metadata)),
                                metadata,
                                data
                            )
                        )
                    except Exception as e:
                        if not self.quiet:
                            self._view.error('Unparsable frame. Dropping: ' + str(e))
                            print s
        except (IOError, EOFError):
            pass