from packetweaver.core import ns
import packetweaver.core.views.text as text


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Displaying text',
        description='Demonstrate the output capabilities',
        tags=[ns.Tag.EXAMPLE],
    )

    _option_list = [
        ns.IpOpt(ns.OptNames.IP_DST, default='127.0.0.1', comment='an IP'),
    ]

    def main(self):
        self._view.success('Display in green')
        self._view.delimiter('A dashed line with title')  # with a fixed len
        self._view.delimiter()  # a dashed line with the same length
        self._view.warning('Display in yellow')
        self._view.error('A red IP: {}'.format(self.ip_dst))
        self._view.fail('Display in cyan')
        self._view.progress('Display in blue')
        self._view.debug('Display in purple')
        self._view.success('Display in your default terminal color')
        self._view.info('{}Display in bold{}'.format(
            self._view.start_effect('bold'), self._view.end_color())
        )
        self._view.info('{}Underline our text{}'.format(
            self._view.start_effect('underline'), self._view.end_color())
        )
        # To mix a color and an effect requires to memorize the previous
        # modification to apply it again after every call of endcolor()
        self._view.warning('Mixing a color and {} in the middle'.format(
            self._view.with_effect(
                'underline', 'an effect', text.Log.colors['warning']))
        )
