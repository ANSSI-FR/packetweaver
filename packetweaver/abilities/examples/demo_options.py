from packetweaver.core import ns
import os


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Demo options',
        description='Demonstrate all available options',
        tags=[ns.Tag.EXAMPLE],
    )

    _option_list = [
        ns.ChoiceOpt('option', ['normal', 'bypass_cache'],
                     default='normal',
                     comment='Define if cache must be bypassed '
                             'when using generators (except "nb")'),
        ns.NumOpt('nb',
                  default=3,
                  comment='Times to display everything'),
        ns.IpOpt(ns.OptNames.IP_DST,
                 default='127.0.0.1',
                 comment='use as default the standardized dst_ip option name'),
        ns.StrOpt('msg',
                  default='my message',
                  comment='A string message'),
        ns.PortOpt(ns.OptNames.PORT_DST,
                   default=2222,
                   comment='A string message'),
        ns.MacOpt(ns.OptNames.MAC_SRC,
                  default='Mac00',
                  comment='Source MAC address'),
        ns.BoolOpt('a_bool',
                   default=True,
                   comment='A True/False value'),
        ns.PathOpt('path',
                   default='pw.ini',
                   comment='Path to an existing file')  # must_exist=True),
    ]

    def display(self):
        for i in range(self.nb):
            self._view.delimiter('Round {}'.format(i+1))
            self._view.info('[{}] - {} - {}'.format(
                self.mac_src, self.ip_dst, self.port_dst)
            )
            self._view.progress('{}'.format(self.msg))
            self._view.debug('{}'.format(self.a_bool))
            self._view.warning('{} (abs: {})'.format(
                self.path, os.path.abspath(self.path))
            )
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
            self._view.progress('{}'.format(self.get_opt('msg',
                                                         bypass_cache=True)))
            self._view.debug('{}'.format(self.get_opt('a_bool',
                                                      bypass_cache=True)))
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
            self._view.error(
                'The number must be greater than 0 ({} given)'.format(self.nb)
            )
            return
        elif self.nb > 2000:
            self._view.warning(
                '{} rounds is quite a lot! '
                'Please try with a lower number.'.format(self.nb)
            )
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
        This ability make use of all the PacketWeaver framework supported
        options.

        Their names are either specified using a label, or a predefined value
        using a OptNames.VAL . The latter solution is preferred as it helps
        getting a clean input interface across different abilities.

        You may play with the different options, modifying their value with
        either:
        - a fixed value
        - a fixed value randomly drawn (e.g RandIP4() for the dst_ip)
        - a random generator (e.g RandIP4)

        The ability will display their value three times so you can see how
        they behave.
        """)
