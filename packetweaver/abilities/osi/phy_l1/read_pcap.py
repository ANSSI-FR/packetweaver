# coding: utf8
import packetweaver.core.ns as ns
try:
    import scapy.layers.l2
    import scapy.utils
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.PathOpt(
            ns.OptNames.PATH_SRC, None,
            'Pcap file from which the packets are read', must_exist=True, readable=True
        )
    ]

    _info = ns.AbilityInfo(
        name='Read from Pcap',
        description='Read frames from PCAP',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L1],
        type=ns.AbilityType.COMPONENT
    )

    def main(self):
        if self.path_src is None:
            self._view.error('Missing filename')
            return

        pcaprd = scapy.utils.PcapReader(self.path_src)

        p = True
        while p:
            p = pcaprd.read_packet(size=65535)
            if p:
                try:
                    self._send(str(p))
                except (IOError, EOFError):
                    break
        pcaprd.close()

    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not HAS_SCAPY:
            l.append('Scapy support missing or broken.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l