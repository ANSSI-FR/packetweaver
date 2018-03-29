# coding: utf8
import packetweaver.core.ns as ns
try:
    import ipaddress
    HAS_NET_LIB = True
except ImportError:
    try:
        import netaddr
        HAS_NET_LIB = True
    except ImportError:
        HAS_NET_LIB = False


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Ping a prefix',
    )

    _option_list = [
        ns.PrefixOpt('prefix', '127.0.0.1/24', 'Ping Destination Prefix'),
    ]

    _dependencies = [('ping', 'sstic', 'Ping a target')]

    def main(self, **kwargs):
        try:
            while True:
                target_ip = self.get_opt('prefix', bypass_cache=True)
                self.get_dependency('ping', ip_dst=target_ip).start()
        except StopIteration:
            pass

    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not HAS_NET_LIB:
            l.append('Python ipaddress or netaddr is required to run this ability. Please install one of them.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l
