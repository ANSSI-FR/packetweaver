import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.NICOpt(ns.OptNames.INPUT_INTERFACE,
                  default=None,
                  comment='Input interface', optional=True),
        ns.NICOpt(ns.OptNames.OUTPUT_INTERFACE,
                  default=None, comment='Output interface', optional=True),
        ns.MacOpt(ns.OptNames.MAC_SRC,
                  default=None, comment='Source Mac', optional=True),
        ns.MacOpt(ns.OptNames.MAC_DST,
                  default=None, comment='Destination Mac', optional=True),
        ns.IpOpt(ns.OptNames.IP_SRC,
                 default=None, comment='Source IP', optional=True),
        ns.IpOpt(ns.OptNames.IP_DST,
                 default=None, comment='Destination IP', optional=True),
        ns.PortOpt(ns.OptNames.PORT_SRC,
                   default=None, comment='Source Port', optional=True),
        ns.PortOpt(ns.OptNames.PORT_DST,
                   default=None, comment='Destination Port', optional=True),
        ns.ChoiceOpt(ns.OptNames.L4PROTOCOL, ['tcp', 'udp'],
                     comment='L4 Protocol over IP', optional=True),
    ]

    _info = ns.AbilityInfo(
        name='Netfilter Config',
        description='Configure Ebtables and IPtables rules to drop '
                    'specified traffic',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L2, ns.Tag.TCP_STACK_L3],
        type=ns.AbilityType.COMPONENT
    )

    @classmethod
    def check_preconditions(cls, module_factory):
        l_dep = []
        if not ns.HAS_IPTC and not ns.HAS_IPTABLES:
            l_dep.append(
                'IPTC support missing or broken and IPtables CLI missing too. '
                'Please install python-iptables, install iptables or proceed '
                'to an update.')
        l_dep += super(Ability, cls).check_preconditions(module_factory)
        return l_dep

    def _configure_firewall_rules(self, iface, oface, mac_src, mac_dst,
                                  ip_src, ip_dst, proto, port_src, port_dst):
        """ Sets the firewall rules to drop traffic that is intercepted!

        :param mac_src: Source MAC address (may be None)
        :param mac_dst: Destination MAC address (may be None)
        :param ip_src: Source IP address (may be None)
        :param ip_dst: Destination IP address (may be None)
        :param proto: Protocol (either "udp" or "tcp" or None)
        :param port_src: Source Port (may be None)
        :param port_dst: Destination Port (may be None)
        :return: the BPF expression as a string
        """
        if not isinstance(mac_src, type(None))\
                or not isinstance(mac_dst, type(None)):
            ns.drop_frames(iface, oface, mac_src, mac_dst)

        if (
            not isinstance(ip_src, type(None))
            or not isinstance(ip_dst, type(None))
            or not isinstance(proto, type(None))
            or not isinstance(port_src, type(None))
            or not isinstance(port_dst, type(None))
        ):
            ns.drop_packets(iface, oface, ip_src, ip_dst, proto,
                            port_src, port_dst, bridge=True)

    def _unconfigure_firewall_rules(self, iface, oface, mac_src, mac_dst,
                                    ip_src, ip_dst, proto, port_src, port_dst):
        """ Sets the firewall rules to drop traffic that is intercepted!

        :param mac_src: Source MAC address (may be None)
        :param mac_dst: Destination MAC address (may be None)
        :param ip_src: Source IP address (may be None)
        :param ip_dst: Destination IP address (may be None)
        :param proto: Protocol (either "udp" or "tcp" or None)
        :param port_src: Source Port (may be None)
        :param port_dst: Destination Port (may be None)
        :return: the BPF expression as a string
        """
        if not isinstance(mac_src, type(None)) \
                or not isinstance(mac_dst, type(None)):
            ns.undrop_frames(iface, oface, mac_src, mac_dst)

        if (
            not isinstance(ip_src, type(None))
            or not isinstance(ip_dst, type(None))
            or not isinstance(proto, type(None))
            or not isinstance(port_src, type(None))
            or not isinstance(port_dst, type(None))
        ):
            ns.undrop_packets(iface, oface, ip_src, ip_dst, proto,
                              port_src, port_dst, bridge=True)

    def main(self):
        self._configure_firewall_rules(
            self.interface, self.outerface,
            self.mac_src, self.mac_dst,
            self.ip_src, self.ip_dst,
            self.protocol,
            self.port_src, self.port_dst,
        )

        self._wait()

        self._unconfigure_firewall_rules(
            self.interface, self.outerface,
            self.mac_src, self.mac_dst,
            self.ip_src, self.ip_dst,
            self.protocol,
            self.port_src, self.port_dst,
        )
