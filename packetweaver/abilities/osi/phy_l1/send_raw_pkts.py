import packetweaver.core.ns as ns
import packetweaver.libs.sys.pcap as pcap_lib


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.NICOpt(ns.OptNames.OUTPUT_INTERFACE, None, 'NIC to send traffic on')
    ]

    _info = ns.AbilityInfo(
        name='Send Raw Frames',
        description='Reads L2 Frames from the pipe and '
                    'writes them on the specified NIC',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L1],
        type=ns.AbilityType.COMPONENT
    )

    @classmethod
    def check_preconditions(cls, module_factory):
        l_dep = []
        if not ns.HAS_PCAPY:
            l_dep.append('Pcapy support missing or broken. '
                         'Please install pcapy or proceed to an update.')
        l_dep += super(Ability, cls).check_preconditions(module_factory)
        return l_dep

    def main(self):
        thr, stop_evt = pcap_lib.send_raw_traffic(self.outerface, self._poll,
                                                  self._recv)

        self._wait()

        stop_evt.set()
        thr.join()
