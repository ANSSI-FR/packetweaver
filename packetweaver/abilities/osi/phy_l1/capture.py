import packetweaver.core.ns as ns
import packetweaver.libs.sys.pcap as pcap_lib


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.StrOpt('bpf',
                  default='',
                  comment='Filter to apply to received frames'),
        ns.NICOpt(ns.OptNames.INPUT_INTERFACE,
                  default=None,
                  comment='NIC to sniff on')
    ]

    _info = ns.AbilityInfo(
        name='Sniff Frames',
        description='Sniff frames and send them in the pipe',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L1],
        type=ns.AbilityType.COMPONENT
    )

    @classmethod
    def check_preconditions(cls, module_factory):
        l_dep = []
        if not ns.HAS_PCAPY:
            l_dep.append(
                'Pcapy support missing or broken. '
                'Please install pcapy or proceed to an update.')
        l_dep += super(Ability, cls).check_preconditions(module_factory)
        return l_dep

    def main(self):
        l_threads = []
        for out in self._builtin_out_pipes:
            thr, cap_stop_evt, _ = pcap_lib.start_capture(
                self.interface, self.bpf, out
            )
            l_threads.append((thr, cap_stop_evt))

        self._wait()

        for t in l_threads:
            t[1].set()
            t[0].join()
