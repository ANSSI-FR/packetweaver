# coding: utf8
import scapy.layers.l2
import scapy.utils
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.PathOpt(ns.OptNames.PATH_DST, None, 'File to write the pcap to', must_exist=False)
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
