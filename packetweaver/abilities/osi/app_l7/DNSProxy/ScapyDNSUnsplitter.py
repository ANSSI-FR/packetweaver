import packetweaver.core.ns as ns
import struct

try:
    import scapy.layers.dns as scapy_dns
    import scapy.layers.l2 as l2
    import scapy.layers.inet as scapy_inet
    import scapy.layers.inet6 as scapy_inet6
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.BoolOpt('quiet',
                   default=True,
                   comment='Whether we should log stuff on error'),
    ]

    _info = ns.AbilityInfo(
        name='DNS Metadata Reverser',
        description='Reads a DNS message + metadata + demux token '
                    'and writes demux token + Ether/DNS',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L5, ns.Tag.THREADED, ns.Tag.DNS],
        type=ns.AbilityType.COMPONENT
    )

    _dependencies = []

    @classmethod
    def check_preconditions(cls, module_factory):
        l_dep = []
        if not HAS_SCAPY:
            l_dep.append('Scapy support missing or broken. '
                         'Please install scapy or proceed to an update.')
        l_dep += super(Ability, cls).check_preconditions(module_factory)
        return l_dep

    def _forge_scapy_response(self, scapy_msg):
        new_msg = l2.Ether(src=scapy_msg[l2.Ether].dst,
                           dst=scapy_msg[l2.Ether].src)
        if scapy_msg.haslayer(scapy_inet.IP):
            new_msg /= scapy_inet.IP(src=scapy_msg[scapy_inet.IP].dst,
                                     dst=scapy_msg[scapy_inet.IP].src)
        else:
            new_msg /= scapy_inet.IPv6(src=scapy_msg[scapy_inet6.IPv6].dst,
                                       dst=scapy_msg[scapy_inet6.IPv6].src)

        new_msg /= scapy_inet.UDP(sport=scapy_msg[scapy_inet.UDP].dport,
                                  dport=scapy_msg[scapy_inet.UDP].sport)

        return new_msg

    def main(self):
        try:
            while not self.is_stopped():
                if self._poll(0.1):
                    s = self._recv()
                    try:
                        demux_tok, metadata_len = struct.unpack('!cH', s[:3])
                        metadata = s[3:metadata_len+3]
                        data = s[metadata_len+3:]

                        parsed_metadata = l2.Ether(metadata)
                        parsed_data = scapy_dns.DNS(data)

                        if demux_tok == '\x00':
                            forged_metadata = self._forge_scapy_response(
                                parsed_metadata
                            )
                            m = forged_metadata / parsed_data
                            self._send(demux_tok + str(m))
                        elif demux_tok == '\xFF':
                            if parsed_metadata.haslayer(scapy_inet.IP):
                                del parsed_metadata[scapy_inet.IP].chksum
                            else:
                                del parsed_metadata[scapy_inet6.IPv6].chksum
                            del parsed_metadata[scapy_inet.UDP].chksum
                            m = parsed_metadata / parsed_data
                            self._send(demux_tok + str(m))
                        else:
                            if not self.quiet:
                                self._view.error(
                                    'Invalid demux token: {:x}.'
                                    ' Dropping.'.format(ord(demux_tok))
                                )
                    except Exception as e:
                        if not self.quiet:
                            self._view.error(
                                'Unparsable frame. Dropping: ' + str(e)
                            )
                            print(s)
        except (IOError, EOFError):
            pass
