# coding: utf8
from packetweaver.core.ns import *


class Ability(AbilityBase):
    _info = AbilityInfo(
        name='Call another Ability',
        description='Demonstrate how to call synchronously another ability',
    )
    _option_list = [
        ChoiceOpt('option', ['normal', 'bypass_cache'], 'normal', 'Define if cache must be bypassed when using generators (except "nb")'),
        StrOpt('msg', 'I was called by another ability', 'Message we want to see in our called ability'),
        NumOpt('nb', 3, 'Times to display everything'),

    ]

    _dependencies = [('abl_demo_opt', 'base', 'Demo options')]

    def main(self, **kwargs):
        # Parameters of the called ability can be set in different way
        abl = self.get_dependency('abl_demo_opt', nb=self.nb, ip_dst='RandIP6', msg=self.msg)
        abl.port_dst = 42
        abl.option = self.option
        abl.set_opt("path", "/bin/true")
        abl.start()
        self._view.info(abl.result())
