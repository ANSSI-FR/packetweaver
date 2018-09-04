from packetweaver.core import ns


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Call another Ability',
        description='Demonstrate how to call synchronously another ability',
    )
    _option_list = [
        ns.ChoiceOpt('option', ['normal', 'bypass_cache'],
                     default='normal',
                     comment='Define if cache must be bypassed when using '
                             'generators (except "nb")'),
        ns.StrOpt('msg', default='I was called by another ability',
                  comment='Message we want to see in our called ability'),
        ns.NumOpt('nb', default=3, comment='Times to display everything'),

    ]

    _dependencies = [('abl_demo_opt', 'base', 'Demo options')]

    def main(self, **kwargs):
        # Parameters of the called ability can be set in different way
        abl = self.get_dependency('abl_demo_opt',
                                  nb=self.nb,
                                  ip_dst='RandIP6',
                                  msg=self.msg)
        abl.port_dst = 42
        abl.option = self.option
        abl.set_opt("path", "/bin/true")
        abl.start()
        self._view.info(abl.result())
