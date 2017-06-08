# encoding: utf-8
import multiprocessing
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.NICOpt(ns.OptNames.INPUT_INTERFACE, None, 'Sniffed interface'),
        ns.NICOpt(ns.OptNames.OUTPUT_INTERFACE, None, 'Injection interface', optional=True),
        ns.MacOpt(ns.OptNames.MAC_SRC, None, 'Source Mac', optional=True),
        ns.MacOpt(ns.OptNames.MAC_DST, None, 'Destination Mac', optional=True),
        ns.IpOpt(ns.OptNames.IP_SRC, None, 'Source IP', optional=True),
        ns.IpOpt(ns.OptNames.IP_DST, None, 'Destination IP', optional=True),
        ns.PortOpt(ns.OptNames.PORT_SRC, None, 'Source Port', optional=True),
        ns.PortOpt(ns.OptNames.PORT_DST, None, 'Destination Port', optional=True),
        ns.ChoiceOpt(ns.OptNames.L4PROTOCOL, ['tcp', 'udp'], comment='L4 Protocol over IP', optional=True),
        ns.StrOpt('bridge', None, '''Specify the bridge to use for sniffing.
            If the bridge does not exist, it will be created
            and the input and output interfaces will be bridged together.''', optional=True),
        ns.BoolOpt('mux', False, '''True if messages to send are prefixed with either \\x00 or \\xFF.
        If a prefix is used, \\x00 means the message is to be sent through the sniffing interface (supposedly back to
        the sender, but who knows?!). If the prefix values \\xFF, then the message is sent through the output interface.
        If no prefix are used and this option values False, then messages are always sent through the ouput interface.
        '''),
        ns.BoolOpt('quiet', True, comment='Whether to log errors.'),
    ]

    _info = ns.AbilityInfo(
        name='Message Interceptor',
        description=
            '''This module sniffs some frames and reports them in the in_pkt channel.
            Original frames might be dropped and new frames can be injected back in.
            If an outerface is specified, the interface and the outerface are bridged together and intercepted frames
            are dropped.''',
        authors=['Florian Maury', ],
        tags=[ns.Tag.INTRUSIVE, ],
        type=ns.AbilityType.COMPONENT
    )

    _dependencies = ['netfilter', 'capture', 'sendraw', 'demux']

    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not ns.HAS_PYROUTE2:
            l.append('PyRoute2 support missing or broken. Please install pyroute2 or proceed to an update.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l

    def _check_parameter_consistency(self):
        """
        Check whether all provided parameters are sensible, including whether related parameters have consistent values
        :return: bool, True if parameter values are consistent
        """
        if (self.port_src is not None or self.port_dst is not None) and self.protocol is None :
            self._view.error('If src port or dst port are defined, a protocol must be specified.')
            return False

        if self.outerface is None and self.mux is True:
            self._view.error('Message are supposed to be prefixed, but output interface is unspecified!?')
            return False

        if self.interface is None:
            self._view.error('An input channel must be defined.')
            return False

        if self.interface is not None and self.outerface is not None and self.interface == self.outerface:
            self._view.error('Input interface and output interface cannot be the same. If you are sniffing and T-mode and you want to inject traffic back, please instanciate your own send_packet ability')
            return False

        br_name = ns.in_bridge(self.interface)
        if br_name is not None and self.bridge is not None and br_name != self.bridge:
            self._view.error('Input interface is already in a different bridge. You might be breaking something here :)')
            return False

        if ns.is_bridge(self.interface):
            self._view.error('A bridge cannot be enslaved to another bridge. Input interface is a bridge.')
            return False

        if self.outerface is not None and ns.is_bridge(self.outerface):
            self._view.error('A bridge cannot be enslaved to another bridge. Output interface is a bridge.')
            return False

        return True

    def _build_bpf(self, mac_src, mac_dst, ip_src, ip_dst, proto, port_src, port_dst):
        """ Builds a BPF from the provided parameters
        :param mac_src: Source MAC address (may be None)
        :param mac_dst: Destination MAC address (may be None)
        :param ip_src: Source IP address (may be None)
        :param ip_dst: Destination IP address (may be None)
        :param proto: Protocol (either "udp" or "tcp" or None)
        :param port_src: Source Port (may be None)
        :param port_dst: Destination Port (may be None)
        :param bidirectional: Bool telling whether the connection must be extracted in one way or in both ways
        :return: the BPF expression as a string
        """
        bpf = set()
        if not isinstance(mac_src, type(None)):
            bpf.add('ether src {}'.format(mac_src))
        if not isinstance(mac_dst, type(None)):
            bpf.add('ether dst {}'.format(mac_dst))
        if not isinstance(ip_src, type(None)):
            bpf.add('src host {}'.format(ip_src))
            bpf.add('ip or ip6')
        if not isinstance(ip_dst, type(None)):
            bpf.add('dst host {}'.format(ip_dst))
            bpf.add('ip or ip6')
        if not isinstance(proto, type(None)):
            bpf.add(proto)
        if not isinstance(port_src, type(None)):
            bpf.add('src port {}'.format(port_src))
        if not isinstance(port_dst, type(None)):
            bpf.add('dst port {}'.format(port_dst))
        return '({})'.format(') and ('.join(list(bpf)))

    def main(self):
        if not self._check_parameter_consistency():
            self._view.warning('Inconsistent parameters')
            return

        bpf_expr = self._build_bpf(
            self.mac_src, self.mac_dst,
            self.ip_src, self.ip_dst,
            self.protocol,
            self.port_src, self.port_dst
        )

        if self.outerface is not None:
            # Bridge only the output NIC at the moment, to create the bridge but not let the traffic go through
            bridge_name = ns.bridge_iface_together(self.outerface, bridge=self.bridge)

            # Configure the firewall to drop relevant frames/packets
            fw_abl = self.get_dependency(
                'netfilter', interface=self.interface, outerface=self.outerface, mac_src=self.mac_src,
                mac_dst=self.mac_dst, ip_src=self.ip_src, ip_dst=self.ip_dst, protocol=self.protocol,
                port_src=self.port_src, port_dst=self.port_dst
            )
            fw_abl.start()

            # Configure the sniffing ability
            sniff_abl = self.get_dependency('capture', bpf=bpf_expr, interface=bridge_name)
            self._transfer_out(sniff_abl)
            sniff_abl.start()

            # Configure the sending ability, if a pipe is provided
            was_source = self._is_source()
            if not was_source:
                if self.mux is True:
                    out1, in1 = multiprocessing.Pipe()
                    send_raw_abl1 = self.get_dependency('sendraw', outerface=self.interface)
                    send_raw_abl1.add_in_pipe(in1)
                    send_raw_abl1.start()

                    out2, in2 = multiprocessing.Pipe()
                    send_raw_abl2 = self.get_dependency('sendraw', outerface=self.outerface)
                    send_raw_abl2.add_in_pipe(in2)
                    send_raw_abl2.start()

                    demux_abl = self.get_dependency('demux')
                    self._transfer_in(demux_abl)
                    demux_abl.start(demux={'\x00': out1, '\xFF': out2}, quiet=self.quiet, deepcopy=False)
                else:
                    send_raw_abl = self.get_dependency('sendraw', outerface=self.outerface)
                    self._transfer_in(send_raw_abl)
                    send_raw_abl.start()
            else:
                send_raw_abl = None

            # Finally adds the input NIC to the bridge, now that relevant packets are dropped, to let through all
            # irrelevant packets
            ns.bridge_iface_together(self.interface, bridge=bridge_name)

            # Wait for the stop event
            self._wait()

            # Stopping Ability
            sniff_abl.stop()
            sniff_abl.join()

            if not was_source:
                if self.mux is True:
                    demux_abl.stop()
                    send_raw_abl1.stop()
                    send_raw_abl2.stop()
                    demux_abl.join()
                    send_raw_abl1.join()
                    send_raw_abl2.join()
                else:
                    send_raw_abl.stop()
                    send_raw_abl.join()

            fw_abl.stop()
            fw_abl.join()

            ns.unbridge(bridge_name)

        else:  # We are only acting on a single interface
            # Configure the sniffing ability
            sniff_abl = self.get_dependency('capture', bpf=bpf_expr, interface=self.interface)
            self._transfer_out(sniff_abl)
            sniff_abl.start()

            was_source = self._is_source()
            if not was_source:
                send_raw_abl = self.get_dependency('sendraw', outerface=self.interface)
                self._transfer_in(send_raw_abl)
                send_raw_abl.start()

            # Wait for the stop event
            self._wait()

            # Stopping Ability
            sniff_abl.stop()
            sniff_abl.join()

            if not was_source:
                send_raw_abl.stop()
                send_raw_abl.join()
