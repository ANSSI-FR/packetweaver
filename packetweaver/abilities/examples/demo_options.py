# coding: utf8
from packetweaver.core.ns import *
import os


class Ability(AbilityBase):
    _info = AbilityInfo(
        name='Demo options',
        description='Demonstrate all available options',
        tags=[Tag.EXAMPLE],
    )

    _option_list = [
        ChoiceOpt('option', ['normal', 'bypass_cache'], 'normal', 'Define if cache must be bypassed when using generators (except "nb")'),
        NumOpt('nb', 3, 'Times to display everything'),
        IpOpt(OptNames.IP_DST, '127.0.0.1', 'A destination IP which named is standardised to dst_ip'),
        StrOpt('msg', 'my message', 'A string message'),
        PortOpt(OptNames.PORT_DST, 2222, 'A string message'),
        MacOpt(OptNames.MAC_SRC, 'Mac00', 'Source MAC address'),
        BoolOpt('a_bool', True, 'A True/False value'),
        PathOpt('path', 'pw.ini', 'Path to an existing file', must_exist=True),
    ]

    def display(self):
        for i in range(self.nb):
            self._view.delimiter('Round {}'.format(i+1))
            self._view.info('[{}] - {} - {}'.format(self.mac_src, self.ip_dst, self.port_dst))
            self._view.progress('{}'.format(self.msg))
            self._view.debug('{}'.format(self.a_bool))
            self._view.warning('{} (abs: {})'.format(self.path, os.path.abspath(self.path)))
            self._view.delimiter()
            self._view.info('')

    def display_bypass_cache(self):
        for i in range(self.nb):
            self._view.delimiter('Round {}'.format(i+1))
            self._view.info(
                '[{}] - {} - {}'.format(
                    self.get_opt('mac_src', bypass_cache=True),
                    self.get_opt('ip_dst', bypass_cache=True),
                    self.get_opt('port_dst', bypass_cache=True),
                )
            )
            self._view.progress('{}'.format(self.get_opt('msg', bypass_cache=True)))
            self._view.debug('{}'.format(self.get_opt('a_bool', bypass_cache=True)))
            self._view.warning(
                '{} (abs: {})'.format(
                    self.get_opt('path', bypass_cache=True),
                    os.path.abspath(self.get_opt('path', bypass_cache=True))
                )
            )
            self._view.delimiter()
            self._view.info('')

    def main(self):
        if self.nb <= 0:
            self._view.error('The number must be greater than 0 ({} given)'.format(self.nb))
            return
        elif self.nb > 2000:
            self._view.warning('{} rounds is quite a lot! Please try with a lower number.'.format(self.nb))
            return

        if self.option == 'normal':
            self.display()
        elif self.option == 'bypass_cache':
            self.display_bypass_cache()

        self._view.success('Done!')
        return 'Done'

    def howto(self):
        self._view.delimiter('Module option demonstration')
        self._view.info("""
        This ability make use of all the PacketWeaver framework supported options.
        
        Their names are either specified using a label, or a predefined value using
        a OptNames.VAL . The latter solution is preferred as it helps getting a 
        clean input interface across different abilities.
        
        You may play with the different options, modifying their value with either:
        - a fixed value
        - a fixed value randomly drawn (e.g RandIP4() for the dst_ip)
        - a random generator (e.g RandIP4)
        
        The ability will display their value three times so you can see how they 
        behave.
        """)

