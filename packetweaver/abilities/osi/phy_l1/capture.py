# coding: utf8
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.StrOpt('bpf', '', 'Filter to apply to received frames'),
        ns.NICOpt(ns.OptNames.INPUT_INTERFACE, None, 'NIC to sniff on')
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
        l = []
        if not ns.HAS_PCAPY:
            l.append('Pcapy support missing or broken. Please install pcapy or proceed to an update.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l

    def main(self):
        l = []
        for out in self._builtin_out_pipes:
            thr, cap_stop_evt, _ = ns.start_capture(self.interface, self.bpf, out)
            l.append((thr, cap_stop_evt))

        self._wait()

        for t in l:
            t[1].set()
            t[0].join()
