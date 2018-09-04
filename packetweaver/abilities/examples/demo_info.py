from packetweaver.core import ns


class Ability(ns.ThreadedAbilityBase):
    _info = ns.AbilityInfo(
        name='Demo info',
        description='Demonstrate all available info metadata',
        tags=['my_custom_tag', ns.Tag.EXAMPLE],
        authors=['John Doe (john.doe@nowhere.com)',
                 'Bob Eau (bob.eau@nowhere.com)'],
        references=[
            ['PacketWeaver online documentation',
             'https://packetweaver.readthedocs.io/'],
            ['PacketWeaver source code',
             'https://github.com/ANSSI-FR/packetweaver']
                    ],
        diffusion='public',
        reliability=ns.Reliability.RELIABLE,
        type=ns.AbilityType.STANDALONE
    )

    def main(self):
        self._view.info('Demonstrates the info metadata '
                        '(run > info to display them).')
