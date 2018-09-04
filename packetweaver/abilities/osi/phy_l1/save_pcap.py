import packetweaver.core.ns as ns
try:
    import scapy.layers.l2
    import scapy.utils
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.PathOpt(ns.OptNames.PATH_DST,
                   default=None,
                   comment='File to write the pcap to',
                   must_exist=False, optional=True)
    ]

    _info = ns.AbilityInfo(
        name='Save to Pcap',
        description='Save received Ether() frames to PCAP',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L1],
        type=ns.AbilityType.COMPONENT
    )

    def main(self):
        if self.path_dst is None:
            self._view.error('Missing filename')
            return

        pcapwr = scapy.utils.PcapWriter(self.path_dst)

        try:
            while not self.is_stopped():
                if self._poll(0.1):
                    s = self._recv()
                    if s:
                        p = scapy.layers.l2.Ether(s)
                        pcapwr.write(p)
        except (IOError, EOFError):
            pass

        pcapwr.close()

    @classmethod
    def check_preconditions(cls, module_factory):
        l_dep = []
        if not HAS_SCAPY:
            l_dep.append(
                'Scapy support missing or broken. '
                'Please install it or proceed to an update.')
        l_dep += super(Ability, cls).check_preconditions(module_factory)
        return l_dep
