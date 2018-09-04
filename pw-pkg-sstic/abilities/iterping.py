import packetweaver.core.ns as ns


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Ping a prefix',
    )

    _option_list = [
        ns.PrefixOpt('prefix',
                     default='127.0.0.1/24',
                     comment='Ping Destination Prefix'),
    ]

    _dependencies = [('ping', 'sstic', 'Ping a target')]

    def main(self, **kwargs):
        try:
            while True:
                target_ip = self.get_opt('prefix', bypass_cache=True)
                self.get_dependency('ping', ip_dst=target_ip).start()
        except StopIteration:
            pass
