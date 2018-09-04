# coding: utf8
import packetweaver.core.ns as ns
import packetweaver.libs.sys.pcap as pcap_lib


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.NICOpt(ns.OptNames.OUTPUT_INTERFACE, None, 'NIC to send traffic on')
    ]

    _info = ns.AbilityInfo(
        name='Send Raw Frames',
        description='Reads L2 Frames from the pipe and writes them on the specified NIC',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L1],
        type=ns.AbilityType.COMPONENT
    )

    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not ns.HAS_PCAPY:
            l.append('Pcapy support missing or broken. Please install pcapy or proceed to an update.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l

    def main(self):
        thr, stop_evt = pcap_lib.send_raw_traffic(self.outerface, self._poll, self._recv)

        self._wait()

        stop_evt.set()
        thr.join()
