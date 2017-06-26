# coding: utf8
from packetweaver.core.ns import *


class Ability(ThreadedAbilityBase):
    _info = AbilityInfo(
        name='Demo info',
        description='Demonstrate all available info metadata',
        tags=['my_custom_tag', Tag.EXAMPLE],
        authors=['John Doe (john.doe@nowhere.com)', 'Bob Eau (bob.eau@nowhere.com)'],
        references=[
            ['PacketWeaver online documentation', 'https://packetweaver.readthedocs.io/'],
            ['PacketWeaver source code', 'https://github.com/ANSSI-FR/packetweaver']
                    ],
        diffusion='public',
        reliability=Reliability.RELIABLE,
        type=AbilityType.STANDALONE
    )

    def main(self):
        self._view.info('Demonstrates the info metadata (run > info to display them).')
